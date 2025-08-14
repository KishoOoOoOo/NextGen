from __future__ import annotations

import socket
import time
from typing import Optional

import httpx

from .models import HealthReport, Project


async def check_health(project: Project) -> HealthReport:
	cfg = project.config.healthcheck
	report = HealthReport()
	start = time.perf_counter()
	try:
		if cfg.type == "none":
			report.status = "unknown"
		elif cfg.type == "process":
			report.status = "healthy" if project.runtime.status == "running" else "unhealthy"
		elif cfg.type == "http":
			if not cfg.url:
				raise ValueError("health.url is required for http healthcheck")
			async with httpx.AsyncClient(timeout=cfg.timeout_seconds) as client:
				resp = await client.get(cfg.url)
				report.http_status = resp.status_code
				report.status = "healthy" if 200 <= resp.status_code < 400 else "unhealthy"
		elif cfg.type == "tcp":
			if not cfg.tcp_host or not cfg.tcp_port:
				raise ValueError("tcp_host and tcp_port are required for tcp healthcheck")
			s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			s.settimeout(cfg.timeout_seconds)
			try:
				s.connect((cfg.tcp_host, int(cfg.tcp_port)))
				report.status = "healthy"
			finally:
				s.close()
	except Exception as e:
		report.status = "unhealthy"
		report.message = str(e)
	finally:
		elapsed_ms = (time.perf_counter() - start) * 1000
		report.latency_ms = round(elapsed_ms, 2)
		from datetime import datetime
		report.last_checked_at = datetime.utcnow()
	return report 