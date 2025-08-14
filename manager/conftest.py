"""
Pytest configuration and fixtures
"""

import pytest
import tempfile
import os
from pathlib import Path
from manager.backend.models import ProjectConfig, Project, ProjectRuntime
from manager.backend.project_store import ProjectStore


@pytest.fixture
def sample_project_config():
    """Create a sample project configuration"""
    return ProjectConfig(
        id="test-project",
        name="Test Project",
        working_dir="/path/to/project",
        command="python",
        args=["app.py"],
        instances=2,
        description="A test project for testing",
        env={"TEST_ENV": "test_value"},
        ports=[8000, 8001],
        log_path="/path/to/logs/test.log"
    )


@pytest.fixture
def sample_project(sample_project_config):
    """Create a sample project"""
    return Project(config=sample_project_config)


@pytest.fixture
def temp_project_store():
    """Create a temporary project store for testing"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write("projects: []")
        temp_file = f.name
    
    store = ProjectStore(Path(temp_file))
    
    yield store
    
    # Cleanup
    try:
        os.unlink(temp_file)
    except OSError:
        pass


@pytest.fixture
def temp_runtime_dir():
    """Create a temporary runtime directory for testing"""
    temp_dir = tempfile.mkdtemp()
    
    yield Path(temp_dir)
    
    # Cleanup
    try:
        import shutil
        shutil.rmtree(temp_dir)
    except OSError:
        pass


@pytest.fixture
def mock_process_manager(temp_runtime_dir):
    """Create a mock process manager for testing"""
    from manager.backend.process_manager import ProcessManager
    
    return ProcessManager(temp_runtime_dir)


@pytest.fixture
def sample_projects():
    """Create a list of sample projects"""
    projects = []
    
    # Project 1
    config1 = ProjectConfig(
        id="project-1",
        name="Project 1",
        working_dir="/path/to/project1",
        command="python",
        args=["app1.py"],
        instances=1
    )
    projects.append(Project(config=config1))
    
    # Project 2
    config2 = ProjectConfig(
        id="project-2",
        name="Project 2",
        working_dir="/path/to/project2",
        command="node",
        args=["server.js"],
        instances=2
    )
    projects.append(Project(config=config2))
    
    # Project 3 (running)
    config3 = ProjectConfig(
        id="project-3",
        name="Project 3",
        working_dir="/path/to/project3",
        command="python",
        args=["app3.py"],
        instances=1
    )
    runtime3 = ProjectRuntime(
        status="running",
        pids=[12345],
        pid=12345
    )
    projects.append(Project(config=config3, runtime=runtime3))
    
    return projects


@pytest.fixture
def mock_psutil():
    """Mock psutil for testing"""
    import pytest
    from unittest.mock import Mock, MagicMock
    
    mock_psutil = Mock()
    
    # Mock Process class
    mock_process = Mock()
    mock_process.cpu_percent.return_value = 25.5
    mock_process.memory_info.return_value = Mock(rss=128 * 1024 * 1024, vms=256 * 1024 * 1024)
    mock_process.num_threads.return_value = 4
    mock_process.create_time = 1640995200.0  # 2022-01-01 00:00:00
    
    # Mock psutil functions
    mock_psutil.Process.return_value = mock_process
    mock_psutil.pid_exists.return_value = True
    mock_psutil.virtual_memory.return_value = Mock(total=8 * 1024 * 1024 * 1024)  # 8GB
    
    return mock_psutil


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Setup test environment before each test"""
    # Set test environment variables
    os.environ['TESTING'] = 'true'
    
    yield
    
    # Cleanup after each test
    # Remove test environment variables
    os.environ.pop('TESTING', None)


def pytest_configure(config):
    """Configure pytest"""
    # Add custom markers
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )
    config.addinivalue_line(
        "markers", "windows: marks tests as Windows-specific"
    )
    config.addinivalue_line(
        "markers", "linux: marks tests as Linux-specific"
    )
    config.addinivalue_line(
        "markers", "mac: marks tests as macOS-specific"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection"""
    # Skip Windows-specific tests on non-Windows platforms
    if os.name != 'nt':
        skip_windows = pytest.mark.skip(reason="Windows-specific test")
        for item in items:
            if "windows" in item.keywords:
                item.add_marker(skip_windows)
    
    # Skip Linux-specific tests on non-Linux platforms
    if os.name == 'nt':
        skip_linux = pytest.mark.skip(reason="Linux-specific test")
        for item in items:
            if "linux" in item.keywords:
                item.add_marker(skip_linux) 