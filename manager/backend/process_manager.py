from __future__ import annotations

import os
import signal
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import psutil

from .models import OperationResult, Project


# Windows-specific flags to hide console window
CREATE_NO_WINDOW = 0x08000000 if os.name == "nt" else 0
DETACHED_PROCESS = 0x00000008 if os.name == "nt" else 0


class ProcessManager:
	"""Run, stop, and inspect managed processes (supports multiple instances)."""

	def __init__(self, runtime_dir: Path) -> None:
		self._runtime_dir = runtime_dir
		self._runtime_dir.mkdir(parents=True, exist_ok=True)
		self._running: Dict[str, List[subprocess.Popen]] = {}

	def _build_env(self, project: Project, override_env: Optional[Dict[str, str]] = None) -> Dict[str, str]:
		env = os.environ.copy()
		env.update(project.config.env or {})
		if override_env:
			env.update(override_env)
		return env

	def _build_command(self, project: Project, override_args: Optional[list[str]] = None) -> list[str]:
		args = override_args if override_args is not None else project.config.args
		cmd = [project.config.command] + list(args)
		return cmd

	def _pid_file(self, project_id: str, idx: int) -> Path:
		return self._runtime_dir / f"{project_id}-{idx}.pid"

	def _write_pid(self, project_id: str, idx: int, pid: int) -> None:
		self._pid_file(project_id, idx).write_text(str(pid), encoding="utf-8")

	def _read_pids(self, project_id: str) -> List[int]:
		pids: List[int] = []
		for idx in range(0, 256):
			pf = self._pid_file(project_id, idx)
			if not pf.exists():
				break
			try:
				pids.append(int(pf.read_text(encoding="utf-8").strip()))
			except Exception:
				continue
		return pids

	def _remove_pid_files(self, project_id: str) -> None:
		for idx in range(0, 256):
			pf = self._pid_file(project_id, idx)
			if pf.exists():
				try:
					pf.unlink()
				except Exception:
					pass
			else:
				break

	def is_running(self, project_id: str) -> bool:
		pids = self._read_pids(project_id)
		return any(pid and psutil.pid_exists(pid) for pid in pids)

	def start(self, project: Project, override_args: Optional[list[str]] = None, override_env: Optional[Dict[str, str]] = None) -> OperationResult:
		if self.is_running(project.config.id):
			return OperationResult(success=False, message="Process already running", project=project)

		command = self._build_command(project, override_args)
		env = self._build_env(project, override_env)
		cwd = Path(project.config.working_dir)
		if not cwd.exists():
			return OperationResult(success=False, message=f"Working dir not found: {cwd}", project=project)

		# Configure output handling
		stdout = subprocess.DEVNULL
		stderr = subprocess.STDOUT
		if project.config.log_path:
			log_path = Path(project.config.log_path)
			log_path.parent.mkdir(parents=True, exist_ok=True)
			stdout = open(log_path, "a", encoding="utf-8", buffering=1)
			stderr = subprocess.STDOUT

		# Use proper flags to hide console window on Windows
		creationflags = 0
		if os.name == "nt":
			creationflags = CREATE_NO_WINDOW | DETACHED_PROCESS
		
		procs: List[subprocess.Popen] = []
		for idx in range(project.config.instances):
			try:
				proc = subprocess.Popen(
					command,
					cwd=str(cwd),
					env=env,
					stdin=subprocess.DEVNULL,
					stdout=stdout,
					stderr=stderr,
					creationflags=creationflags,
					startupinfo=self._get_startupinfo() if os.name == "nt" else None,
				)
				procs.append(proc)
			except FileNotFoundError as e:
				return OperationResult(success=False, message=f"Executable not found: {e}", project=project)
			except Exception as e:
				return OperationResult(success=False, message=f"Failed to start: {e}", project=project)

		self._running[project.config.id] = procs
		project.runtime.pids = [p.pid for p in procs]
		project.runtime.pid = project.runtime.pids[0] if project.runtime.pids else None
		for idx, proc in enumerate(procs):
			self._write_pid(project.config.id, idx, proc.pid)
		project.runtime.status = "running"
		project.runtime.started_at = datetime.utcnow()
		return OperationResult(success=True, message="Started", project=project)

	def _get_startupinfo(self):
		"""Get startup info to hide console window on Windows"""
		if os.name == "nt":
			import subprocess
			startupinfo = subprocess.STARTUPINFO()
			startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
			startupinfo.wShowWindow = subprocess.SW_HIDE
			return startupinfo
		return None

	def stop(self, project: Project, timeout_seconds: int = 10) -> OperationResult:
		pids = self._read_pids(project.config.id)
		if not pids:
			return OperationResult(success=True, message="Already stopped", project=project)

		for pid in pids:
			try:
				process = psutil.Process(pid)
				if os.name == "nt":
					process.send_signal(signal.SIGTERM)
				else:
					process.terminate()
				try:
					process.wait(timeout=timeout_seconds)
				except psutil.TimeoutExpired:
					process.kill()
			except psutil.Error:
				pass
		self._remove_pid_files(project.config.id)
		project.runtime.status = "stopped"
		project.runtime.stopped_at = datetime.utcnow()
		project.runtime.last_exit_code = None
		project.runtime.pids = []
		project.runtime.pid = None
		return OperationResult(success=True, message="Stopped", project=project)

	def status(self, project: Project) -> Project:
		pids = self._read_pids(project.config.id)
		alive = [pid for pid in pids if pid and psutil.pid_exists(pid)]
		project.runtime.pids = alive
		project.runtime.pid = alive[0] if alive else None
		project.runtime.status = "running" if alive else "stopped"
		
		# Update uptime if running
		if alive and project.runtime.started_at:
			project.runtime.uptime_seconds = (datetime.utcnow() - project.runtime.started_at).total_seconds()
		
		return project

	def collect_metrics(self, project: Project) -> Project:
		pids = self._read_pids(project.config.id)
		alive = [pid for pid in pids if pid and psutil.pid_exists(pid)]
		if not alive:
			m = project.runtime.metrics
			m.cpu_percent = 0.0
			m.memory_rss_mb = 0.0
			m.memory_vms_mb = 0.0
			m.threads = 0
			m.uptime_seconds = None
			return project

		total_cpu = 0.0
		total_rss = 0
		total_vms = 0
		total_threads = 0
		first_create = None
		
		for pid in alive:
			try:
				p = psutil.Process(pid)
				with p.oneshot():
					# Get CPU usage with interval to get accurate reading
					cpu_percent = p.cpu_percent(interval=0.1)
					total_cpu += cpu_percent
					
					# Get memory info
					mi = p.memory_info()
					total_rss += mi.rss
					total_vms += mi.vms
					total_threads += p.num_threads()
					
					# Get creation time
					ct = getattr(p, "create_time", None)
					if ct and (first_create is None or ct < first_create):
						first_create = ct
			except psutil.Error:
				continue
		
		m = project.runtime.metrics
		m.cpu_percent = round(float(total_cpu), 2)
		m.memory_rss_mb = round(total_rss / (1024 * 1024), 2)
		m.memory_vms_mb = round(total_vms / (1024 * 1024), 2)
		m.threads = int(total_threads)
		m.uptime_seconds = float(time.time() - first_create) if first_create else None
		
		# Calculate memory percentage
		try:
			system_memory = psutil.virtual_memory()
			m.memory_percent = round((total_rss / system_memory.total) * 100, 2)
		except:
			m.memory_percent = 0.0
		
		return project 