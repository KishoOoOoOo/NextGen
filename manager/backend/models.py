from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field


HealthType = Literal["http", "tcp", "process", "none"]


class HealthcheckConfig(BaseModel):
	"""Configuration for project health checking."""
	type: HealthType = Field(default="process")
	url: Optional[str] = None
	tcp_host: Optional[str] = None
	tcp_port: Optional[int] = None
	interval_seconds: int = Field(default=10, ge=2, le=3600)
	timeout_seconds: int = Field(default=3, ge=1, le=60)


class RestartPolicy(BaseModel):
	autorestart: bool = True
	restart_delay_seconds: int = Field(default=5, ge=1, le=3600)
	max_restarts_per_hour: int = Field(default=10, ge=0, le=1000)


class ProjectConfig(BaseModel):
	"""Static configuration of a managed project."""
	id: str = Field(description="Unique identifier for the project")
	name: str
	working_dir: str
	command: str = Field(description="Executable or interpreter (e.g., python, uvicorn)")
	args: List[str] = Field(default_factory=list)
	python_path: Optional[str] = Field(default=None, description="Custom Python interpreter path if needed")
	env: Dict[str, str] = Field(default_factory=dict)
	log_path: Optional[str] = None
	ports: List[int] = Field(default_factory=list)
	healthcheck: HealthcheckConfig = Field(default_factory=HealthcheckConfig)
	restart_policy: RestartPolicy = Field(default_factory=RestartPolicy)
	start_on_boot: bool = False
	instances: int = Field(default=1, ge=1, le=64)
	actions: Dict[str, List[str]] = Field(default_factory=dict, description="Custom actions: name -> args list to run with 'command'")
	description: Optional[str] = None


RuntimeStatus = Literal[
	"stopped",
	"starting",
	"running",
	"unhealthy",
	"crashed",
	"stopping",
]


class HealthReport(BaseModel):
	status: Literal["unknown", "healthy", "unhealthy"] = "unknown"
	last_checked_at: Optional[datetime] = None
	latency_ms: Optional[float] = None
	http_status: Optional[int] = None
	message: Optional[str] = None


class ProcessMetrics(BaseModel):
	cpu_percent: float = 0.0
	memory_rss_mb: float = 0.0
	memory_vms_mb: float = 0.0
	memory_percent: float = 0.0
	threads: int = 0
	uptime_seconds: Optional[float] = None


class ProjectRuntime(BaseModel):
	pid: Optional[int] = None
	pids: List[int] = Field(default_factory=list)
	status: RuntimeStatus = "stopped"
	started_at: Optional[datetime] = None
	stopped_at: Optional[datetime] = None
	last_exit_code: Optional[int] = None
	restarts_in_window: int = 0
	restarts_total: int = 0
	window_started_at: Optional[datetime] = None
	metrics: ProcessMetrics = Field(default_factory=ProcessMetrics)
	health: HealthReport = Field(default_factory=HealthReport)


class Project(BaseModel):
	config: ProjectConfig
	runtime: ProjectRuntime = Field(default_factory=ProjectRuntime)


# API Schemas
class CreateOrUpdateProjectRequest(BaseModel):
	config: ProjectConfig


class StartProjectRequest(BaseModel):
	override_args: Optional[List[str]] = None
	override_env: Optional[Dict[str, str]] = None
	instances: Optional[int] = None


class TailLogsResponse(BaseModel):
	lines: List[str]
	truncated: bool = False


class OperationResult(BaseModel):
	success: bool
	message: Optional[str] = None
	project: Optional[Project] = None 