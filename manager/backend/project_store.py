from __future__ import annotations

import threading
from pathlib import Path
from typing import Dict, List, Optional

import yaml
from pydantic import ValidationError

from .models import Project, ProjectConfig, ProjectRuntime


class ProjectStore:
	"""Simple YAML-backed store for project configurations and lightweight runtime mirrors."""

	def __init__(self, yaml_path: Path) -> None:
		self._yaml_path = yaml_path
		self._lock = threading.RLock()
		self._projects: Dict[str, Project] = {}
		self._yaml_path.parent.mkdir(parents=True, exist_ok=True)
		self._load_from_disk()

	def _load_from_disk(self) -> None:
		if not self._yaml_path.exists():
			self._projects = {}
			return
		try:
			with self._yaml_path.open("r", encoding="utf-8") as f:
				data = yaml.safe_load(f) or {}
				# Ensure data is a dict
				if not isinstance(data, dict):
					data = {}
				projects: Dict[str, Project] = {}
				items = data.get("projects", []) if isinstance(data, dict) else []
				for item in items:
					try:
						config = ProjectConfig(**item)
						projects[config.id] = Project(config=config, runtime=ProjectRuntime())
					except ValidationError:
						continue
				self._projects = projects
		except Exception:
			# On any YAML read/parse error, treat as empty store
			self._projects = {}

	def _write_to_disk(self) -> None:
		data = {"projects": [p.config.model_dump() for p in self._projects.values()]}
		with self._yaml_path.open("w", encoding="utf-8") as f:
			yaml.safe_dump(data, f, sort_keys=False, allow_unicode=True)

	def list_projects(self) -> List[Project]:
		with self._lock:
			return list(self._projects.values())

	def get_project(self, project_id: str) -> Optional[Project]:
		with self._lock:
			return self._projects.get(project_id)

	def upsert_project(self, config: ProjectConfig) -> Project:
		with self._lock:
			project = self._projects.get(config.id)
			if project is None:
				project = Project(config=config, runtime=ProjectRuntime())
				self._projects[config.id] = project
			else:
				project.config = config
			self._write_to_disk()
			return project

	def delete_project(self, project_id: str) -> bool:
		with self._lock:
			if project_id in self._projects:
				del self._projects[project_id]
				self._write_to_disk()
				return True
			return False


def default_store_path() -> Path:
	return Path("manager/data/projects.yaml").resolve() 