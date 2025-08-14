from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
from typing import List
from datetime import datetime

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from .models import (
	CreateOrUpdateProjectRequest,
	Project,
	StartProjectRequest,
	TailLogsResponse,
)
from .orchestrator import BroadcastHub, Orchestrator
from .process_manager import ProcessManager
from .project_store import ProjectStore, default_store_path


APP_TITLE = "OrchestratorX"
app = FastAPI(title=APP_TITLE, version="0.2.0")

app.add_middleware(
	CORSMiddleware,
	allow_origins=["*"],
	allow_methods=["*"],
	allow_headers=["*"],
)


DATA_DIR = Path("manager/data").resolve()
RUNTIME_DIR = DATA_DIR / "runtime"
STORE = ProjectStore(default_store_path())
PROC = ProcessManager(RUNTIME_DIR)
HUB = BroadcastHub()
ORCH = Orchestrator(STORE, PROC, HUB)

# Static UI
STATIC_DIR = Path(__file__).parent / "static"
STATIC_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/ui", StaticFiles(directory=str(STATIC_DIR), html=True), name="ui")


@app.on_event("startup")
async def _startup():
	await ORCH.start()


@app.on_event("shutdown")
async def _shutdown():
	await ORCH.stop()


@app.get("/")
async def root_redirect():
	return RedirectResponse(url="/ui/")


@app.get("/dashboard")
async def dashboard_redirect():
	return RedirectResponse(url="/ui/dashboard.html")


@app.get("/api/system/stats")
async def get_system_stats():
	"""Get overall system statistics"""
	projects = [PROC.status(p) for p in STORE.list_projects()]
	
	total_projects = len(projects)
	running_projects = len([p for p in projects if p.runtime.status == "running"])
	stopped_projects = len([p for p in projects if p.runtime.status == "stopped"])
	unhealthy_projects = len([p for p in projects if p.runtime.health.status == "unhealthy"])
	total_restarts = sum(p.runtime.restarts_total for p in projects)
	
	# Calculate total system metrics
	total_cpu = 0.0
	total_memory = 0.0
	total_memory_percent = 0.0
	
	for p in projects:
		if p.runtime.status == "running" and p.runtime.metrics:
			PROC.collect_metrics(p)  # Ensure fresh metrics
			total_cpu += p.runtime.metrics.cpu_percent or 0
			total_memory += p.runtime.metrics.memory_rss_mb or 0
			total_memory_percent += p.runtime.metrics.memory_percent or 0
	
	# Get system information
	import psutil
	system_cpu = psutil.cpu_percent(interval=1)
	system_memory = psutil.virtual_memory()
	system_disk = psutil.disk_usage('/')
	
	return {
		"total_projects": total_projects,
		"running_projects": running_projects,
		"stopped_projects": stopped_projects,
		"unhealthy_projects": unhealthy_projects,
		"total_restarts": total_restarts,
		"total_cpu_percent": round(total_cpu, 2),
		"total_memory_mb": round(total_memory, 2),
		"total_memory_percent": round(total_memory_percent, 2),
		"system_cpu_percent": round(system_cpu, 2),
		"system_memory_percent": round(system_memory.percent, 2),
		"system_memory_total_gb": round(system_memory.total / (1024**3), 2),
		"system_memory_available_gb": round(system_memory.available / (1024**3), 2),
		"system_disk_percent": round(system_disk.percent, 2),
		"system_disk_total_gb": round(system_disk.total / (1024**3), 2),
		"system_disk_free_gb": round(system_disk.free / (1024**3), 2),
		"uptime_hours": 24  # Placeholder - could track actual uptime
	}


@app.post("/api/detect-project-files")
async def detect_project_files(body: dict):
	"""Detect executable files and logs in a project directory"""
	folder_path = body.get("folder_path")
	if not folder_path:
		raise HTTPException(status_code=400, detail="folder_path is required")
	
	try:
		project_dir = Path(folder_path)
		if not project_dir.exists() or not project_dir.is_dir():
			raise HTTPException(status_code=404, detail="Directory not found")
		
		files = list(project_dir.glob("*"))
		file_names = [f.name for f in files if f.is_file()]
		
		# Detect main executable file
		main_file = None
		command = "python"
		
		if "main.py" in file_names:
			main_file = "main.py"
			command = "python"
		elif "app.py" in file_names:
			main_file = "app.py"
			command = "python"
		elif "index.js" in file_names:
			main_file = "index.js"
			command = "node"
		elif "package.json" in file_names:
			main_file = "package.json"
			command = "npm"
		elif "server.py" in file_names:
			main_file = "server.py"
			command = "python"
		
		# Detect log files
		log_files = [f for f in file_names if f.endswith(('.log', '.txt')) and 'log' in f.lower()]
		log_path = log_files[0] if log_files else None
		
		return {
			"main_file": main_file,
			"command": command,
			"log_path": log_path,
			"detected_files": file_names
		}
		
	except Exception as e:
		raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/projects/verify-path")
async def verify_project_path(body: dict):
	"""Verify that a given working_dir exists on the server."""
	p = body.get("working_dir")
	if not p:
		raise HTTPException(status_code=400, detail="working_dir is required")
	try:
		pp = Path(p)
		return {"exists": pp.exists(), "is_dir": pp.is_dir(), "path": str(pp.resolve())}
	except Exception as e:
		raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/projects", response_model=List[Project])
async def list_projects() -> List[Project]:
	projects = [PROC.status(p) for p in STORE.list_projects()]
	return projects


@app.post("/api/projects", response_model=Project)
async def upsert_project(body: CreateOrUpdateProjectRequest) -> Project:
	project = STORE.upsert_project(body.config)
	return PROC.status(project)


@app.delete("/api/projects/{project_id}")
async def delete_project(project_id: str):
	deleted = STORE.delete_project(project_id)
	if not deleted:
		raise HTTPException(status_code=404, detail="Project not found")
	return JSONResponse({"success": True})


@app.post("/api/projects/{project_id}/start", response_model=Project)
async def start_project(project_id: str, body: StartProjectRequest | None = None):
	project = STORE.get_project(project_id)
	if not project:
		raise HTTPException(status_code=404, detail="Project not found")
	if body and body.instances:
		project.config.instances = max(1, min(body.instances, 64))
	result = PROC.start(project, override_args=(body.override_args if body else None), override_env=(body.override_env if body else None))
	if not result.success:
		raise HTTPException(status_code=400, detail=result.message)
	return PROC.status(result.project)  # type: ignore[arg-type]


@app.post("/api/projects/{project_id}/stop", response_model=Project)
async def stop_project(project_id: str):
	project = STORE.get_project(project_id)
	if not project:
		raise HTTPException(status_code=404, detail="Project not found")
	result = PROC.stop(project)
	if not result.success:
		raise HTTPException(status_code=400, detail=result.message)
	return PROC.status(result.project)  # type: ignore[arg-type]


@app.post("/api/projects/{project_id}/restart", response_model=Project)
async def restart_project(project_id: str):
	project = STORE.get_project(project_id)
	if not project:
		raise HTTPException(status_code=404, detail="Project not found")
	PROC.stop(project)
	result = PROC.start(project)
	if not result.success:
		raise HTTPException(status_code=400, detail=result.message)
	return PROC.status(result.project)  # type: ignore[arg-type]


@app.post("/api/projects/{project_id}/actions/{action}")
async def run_action(project_id: str, action: str):
	project = STORE.get_project(project_id)
	if not project:
		raise HTTPException(status_code=404, detail="Project not found")
	args = project.config.actions.get(action)
	if not args:
		raise HTTPException(status_code=404, detail="Action not found")
	# Run action once (not managed), return output
	import subprocess
	try:
		proc = subprocess.run([project.config.command] + args, cwd=project.config.working_dir, capture_output=True, text=True, timeout=120)
		return {"code": proc.returncode, "stdout": proc.stdout, "stderr": proc.stderr}
	except Exception as e:
		raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/projects/{project_id}", response_model=Project)
async def get_project(project_id: str) -> Project:
	project = STORE.get_project(project_id)
	if not project:
		raise HTTPException(status_code=404, detail="Project not found")
	return PROC.status(project)


@app.get("/api/system/metrics")
async def get_system_metrics():
	"""Get detailed system metrics"""
	import psutil
	
	# CPU metrics
	cpu_percent = psutil.cpu_percent(interval=1)
	cpu_count = psutil.cpu_count()
	cpu_freq = psutil.cpu_freq()
	
	# Memory metrics
	memory = psutil.virtual_memory()
	
	# Disk metrics
	disk = psutil.disk_usage('/')
	
	# Network metrics
	network = psutil.net_io_counters()
	
	# Load average (Unix only)
	load_avg = None
	if hasattr(psutil, 'getloadavg'):
		try:
			load_avg = psutil.getloadavg()
		except:
			pass
	
	return {
		"cpu": {
			"percent": round(cpu_percent, 2),
			"count": cpu_count,
			"frequency_mhz": round(cpu_freq.current, 2) if cpu_freq else None,
			"frequency_max_mhz": round(cpu_freq.max, 2) if cpu_freq else None
		},
		"memory": {
			"total_gb": round(memory.total / (1024**3), 2),
			"available_gb": round(memory.available / (1024**3), 2),
			"used_gb": round(memory.used / (1024**3), 2),
			"percent": round(memory.percent, 2)
		},
		"disk": {
			"total_gb": round(disk.total / (1024**3), 2),
			"used_gb": round(disk.used / (1024**3), 2),
			"free_gb": round(disk.free / (1024**3), 2),
			"percent": round(disk.percent, 2)
		},
		"network": {
			"bytes_sent": network.bytes_sent,
			"bytes_recv": network.bytes_recv,
			"packets_sent": network.packets_sent,
			"packets_recv": network.packets_recv
		},
		"load_average": load_avg,
		"timestamp": datetime.utcnow().isoformat()
	}


@app.get("/api/projects/{project_id}/metrics", response_model=Project)
async def get_metrics(project_id: str) -> Project:
	project = STORE.get_project(project_id)
	if not project:
		raise HTTPException(status_code=404, detail="Project not found")
	
	# Update status and collect fresh metrics
	PROC.status(project)
	if project.runtime.status == "running":
		PROC.collect_metrics(project)
	
	return project


@app.get("/api/projects/{project_id}/logs", response_model=TailLogsResponse)
async def tail_logs(project_id: str, lines: int = 200) -> TailLogsResponse:
	project = STORE.get_project(project_id)
	if not project:
		raise HTTPException(status_code=404, detail="Project not found")
	log_path = project.config.log_path
	if not log_path:
		return TailLogsResponse(lines=["No log_path configured for this project"], truncated=False)
	p = Path(log_path)
	if not p.exists():
		return TailLogsResponse(lines=["Log file not found"], truncated=False)
	# Simple and robust tail
	max_read_bytes = 256 * 1024
	try:
		file_size = p.stat().st_size
		start_pos = max(0, file_size - max_read_bytes)
		with p.open("rb") as f:
			f.seek(start_pos)
			data = f.read()
			text = data.decode("utf-8", errors="replace")
			rows = text.splitlines()[-lines:]
			return TailLogsResponse(lines=rows, truncated=len(text.splitlines()) > len(rows))
	except Exception:
		return TailLogsResponse(lines=["Failed to read log"], truncated=False)


@app.websocket("/ws")
async def ws_handler(ws: WebSocket):
	await ws.accept()

	async def push(projects: list[Project]):
		try:
			payload = json.dumps([p.model_dump() for p in projects], default=str)
			await ws.send_text(payload)
		except RuntimeError:
			pass

	HUB.subscribe(push)
	try:
		# send initial snapshot
		projects = [PROC.status(p) for p in STORE.list_projects()]
		await push(projects)
		while True:
			await ws.receive_text()
	except WebSocketDisconnect:
		pass
	finally:
		HUB.unsubscribe(push)


@app.get("/healthz")
async def healthz():
	return {"ok": True, "app": APP_TITLE}


def run():
	import uvicorn
	uvicorn.run("manager.backend.app:app", host="0.0.0.0", port=8077, reload=False)


if __name__ == "__main__":
	run()