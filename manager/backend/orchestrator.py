from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from typing import Awaitable, Callable, List, Set

from .health import check_health
from .models import Project
from .process_manager import ProcessManager
from .project_store import ProjectStore


class BroadcastHub:
	def __init__(self) -> None:
		self._subscribers: Set[Callable[[list[Project]], Awaitable[None]]] = set()

	def subscribe(self, cb: Callable[[list[Project]], Awaitable[None]]) -> None:
		self._subscribers.add(cb)

	def unsubscribe(self, cb: Callable[[list[Project]], Awaitable[None]]) -> None:
		self._subscribers.discard(cb)

	async def broadcast(self, projects: list[Project]) -> None:
		for cb in list(self._subscribers):
			try:
				await cb(projects)
			except Exception:
				self._subscribers.discard(cb)


class Orchestrator:
	def __init__(self, store: ProjectStore, proc: ProcessManager, hub: BroadcastHub) -> None:
		self._store = store
		self._proc = proc
		self._hub = hub
		self._task: asyncio.Task | None = None
		self._stopped = asyncio.Event()
		self._last_metrics_update = datetime.utcnow()
		self._last_health_update = datetime.utcnow()

	async def start(self) -> None:
		self._stopped.clear()
		self._task = asyncio.create_task(self._run())

	async def stop(self) -> None:
		self._stopped.set()
		if self._task:
			await asyncio.wait([self._task])

	async def _run(self) -> None:
		while not self._stopped.is_set():
			try:
				projects = self._store.list_projects()
				
				# Update status for all projects
				for p in projects:
					self._proc.status(p)
				
				# Update metrics every 5 seconds
				now = datetime.utcnow()
				if (now - self._last_metrics_update).total_seconds() >= 5:
					for p in projects:
						if p.runtime.status == "running":
							self._proc.collect_metrics(p)
					self._last_metrics_update = now
				
				# Update health every 10 seconds
				if (now - self._last_health_update).total_seconds() >= 10:
					for p in projects:
						if p.runtime.status == "running":
							try:
								report = await check_health(p)
								p.runtime.health = report
								
								# Auto-restart if unhealthy and autorestart is enabled
								if (report.status == "unhealthy" and 
									p.config.restart_policy.autorestart):
									await self._maybe_restart(p)
							except Exception as e:
								# Log health check error but don't fail
								print(f"Health check failed for {p.config.id}: {e}")
					self._last_health_update = now
				
				# Broadcast snapshot
				await self._hub.broadcast([p for p in projects])
				
				# Wait before next iteration
				await asyncio.sleep(2)
				
			except Exception as e:
				print(f"Orchestrator error: {e}")
				await asyncio.sleep(5)  # Wait longer on error

	async def _maybe_restart(self, project: Project) -> None:
		policy = project.config.restart_policy
		
		# Basic sliding window 1 hour
		now = datetime.utcnow()
		window_start = project.runtime.window_started_at or now
		
		if (now - window_start) > timedelta(hours=1):
			project.runtime.window_started_at = now
			project.runtime.restarts_in_window = 0
		
		if project.runtime.restarts_in_window >= policy.max_restarts_per_hour:
			print(f"Max restarts reached for {project.config.id}")
			return
		
		# Perform restart
		print(f"Restarting unhealthy project: {project.config.id}")
		self._proc.stop(project)
		await asyncio.sleep(policy.restart_delay_seconds)
		result = self._proc.start(project)
		
		if result.success:
			project.runtime.restarts_in_window += 1
			project.runtime.restarts_total += 1
			print(f"Successfully restarted {project.config.id}")
		else:
			print(f"Failed to restart {project.config.id}: {result.message}") 