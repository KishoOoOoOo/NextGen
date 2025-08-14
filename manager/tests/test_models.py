"""
Tests for models
"""

import pytest
from manager.backend.models import (
    ProjectConfig,
    HealthcheckConfig,
    RestartPolicy,
    Project,
    ProjectRuntime,
    ProcessMetrics,
    HealthReport,
)


class TestProjectConfig:
    def test_project_config_creation(self):
        """Test creating a project configuration"""
        config = ProjectConfig(
            id="test-project",
            name="Test Project",
            working_dir="/path/to/project",
            command="python",
            args=["app.py"],
            instances=2,
            description="A test project"
        )
        
        assert config.id == "test-project"
        assert config.name == "Test Project"
        assert config.working_dir == "/path/to/project"
        assert config.command == "python"
        assert config.args == ["app.py"]
        assert config.instances == 2
        assert config.description == "A test project"
    
    def test_project_config_defaults(self):
        """Test project configuration defaults"""
        config = ProjectConfig(
            id="test-project",
            name="Test Project",
            working_dir="/path/to/project",
            command="python"
        )
        
        assert config.args == []
        assert config.instances == 1
        assert config.env == {}
        assert config.ports == []
        assert config.description is None
        assert config.log_path is None
    
    def test_project_config_validation(self):
        """Test project configuration validation"""
        # Should not raise an exception
        config = ProjectConfig(
            id="test-project",
            name="Test Project",
            working_dir="/path/to/project",
            command="python"
        )
        assert config is not None


class TestHealthcheckConfig:
    def test_healthcheck_config_creation(self):
        """Test creating a healthcheck configuration"""
        config = HealthcheckConfig(
            type="http",
            url="http://localhost:8000/health",
            interval_seconds=30,
            timeout_seconds=5
        )
        
        assert config.type == "http"
        assert config.url == "http://localhost:8000/health"
        assert config.interval_seconds == 30
        assert config.timeout_seconds == 5
    
    def test_healthcheck_config_defaults(self):
        """Test healthcheck configuration defaults"""
        config = HealthcheckConfig()
        
        assert config.type == "process"
        assert config.url is None
        assert config.tcp_host is None
        assert config.tcp_port is None
        assert config.interval_seconds == 10
        assert config.timeout_seconds == 3


class TestRestartPolicy:
    def test_restart_policy_creation(self):
        """Test creating a restart policy"""
        policy = RestartPolicy(
            autorestart=True,
            restart_delay_seconds=10,
            max_restarts_per_hour=5
        )
        
        assert policy.autorestart is True
        assert policy.restart_delay_seconds == 10
        assert policy.max_restarts_per_hour == 5
    
    def test_restart_policy_defaults(self):
        """Test restart policy defaults"""
        policy = RestartPolicy()
        
        assert policy.autorestart is True
        assert policy.restart_delay_seconds == 5
        assert policy.max_restarts_per_hour == 10


class TestProcessMetrics:
    def test_process_metrics_creation(self):
        """Test creating process metrics"""
        metrics = ProcessMetrics(
            cpu_percent=25.5,
            memory_rss_mb=128.0,
            memory_vms_mb=256.0,
            memory_percent=12.5,
            threads=4,
            uptime_seconds=3600.0
        )
        
        assert metrics.cpu_percent == 25.5
        assert metrics.memory_rss_mb == 128.0
        assert metrics.memory_vms_mb == 256.0
        assert metrics.memory_percent == 12.5
        assert metrics.threads == 4
        assert metrics.uptime_seconds == 3600.0
    
    def test_process_metrics_defaults(self):
        """Test process metrics defaults"""
        metrics = ProcessMetrics()
        
        assert metrics.cpu_percent == 0.0
        assert metrics.memory_rss_mb == 0.0
        assert metrics.memory_vms_mb == 0.0
        assert metrics.memory_percent == 0.0
        assert metrics.threads == 0
        assert metrics.uptime_seconds is None


class TestHealthReport:
    def test_health_report_creation(self):
        """Test creating a health report"""
        from datetime import datetime
        
        now = datetime.utcnow()
        report = HealthReport(
            status="healthy",
            last_checked_at=now,
            latency_ms=150.5,
            http_status=200,
            message="All systems operational"
        )
        
        assert report.status == "healthy"
        assert report.last_checked_at == now
        assert report.latency_ms == 150.5
        assert report.http_status == 200
        assert report.message == "All systems operational"
    
    def test_health_report_defaults(self):
        """Test health report defaults"""
        report = HealthReport()
        
        assert report.status == "unknown"
        assert report.last_checked_at is None
        assert report.latency_ms is None
        assert report.http_status is None
        assert report.message is None


class TestProjectRuntime:
    def test_project_runtime_creation(self):
        """Test creating project runtime"""
        from datetime import datetime
        
        now = datetime.utcnow()
        runtime = ProjectRuntime(
            pid=12345,
            pids=[12345, 12346],
            status="running",
            started_at=now,
            restarts_total=2,
            restarts_in_window=1
        )
        
        assert runtime.pid == 12345
        assert runtime.pids == [12345, 12346]
        assert runtime.status == "running"
        assert runtime.started_at == now
        assert runtime.restarts_total == 2
        assert runtime.restarts_in_window == 1
    
    def test_project_runtime_defaults(self):
        """Test project runtime defaults"""
        runtime = ProjectRuntime()
        
        assert runtime.pid is None
        assert runtime.pids == []
        assert runtime.status == "stopped"
        assert runtime.started_at is None
        assert runtime.stopped_at is None
        assert runtime.last_exit_code is None
        assert runtime.restarts_in_window == 0
        assert runtime.restarts_total == 0
        assert runtime.window_started_at is None


class TestProject:
    def test_project_creation(self):
        """Test creating a project"""
        config = ProjectConfig(
            id="test-project",
            name="Test Project",
            working_dir="/path/to/project",
            command="python"
        )
        
        project = Project(config=config)
        
        assert project.config == config
        assert isinstance(project.runtime, ProjectRuntime)
        assert isinstance(project.runtime.metrics, ProcessMetrics)
        assert isinstance(project.runtime.health, HealthReport)
    
    def test_project_with_runtime(self):
        """Test creating a project with custom runtime"""
        config = ProjectConfig(
            id="test-project",
            name="Test Project",
            working_dir="/path/to/project",
            command="python"
        )
        
        runtime = ProjectRuntime(status="running")
        project = Project(config=config, runtime=runtime)
        
        assert project.config == config
        assert project.runtime == runtime 