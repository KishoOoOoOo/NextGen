"""
Tests for project store
"""

import pytest
import tempfile
import os
from pathlib import Path
from manager.backend.models import ProjectConfig, Project, ProjectRuntime
from manager.backend.project_store import ProjectStore


class TestProjectStore:
    @pytest.fixture
    def temp_yaml_file(self):
        """Create a temporary YAML file for testing"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
projects:
  - id: "test-project-1"
    name: "Test Project 1"
    working_dir: "/path/to/project1"
    command: "python"
    args: ["app.py"]
    instances: 1
    description: "First test project"
    
  - id: "test-project-2"
    name: "Test Project 2"
    working_dir: "/path/to/project2"
    command: "node"
    args: ["server.js"]
    instances: 2
    description: "Second test project"
""")
            temp_file = f.name
        
        yield Path(temp_file)
        
        # Cleanup
        try:
            os.unlink(temp_file)
        except OSError:
            pass
    
    @pytest.fixture
    def empty_yaml_file(self):
        """Create an empty YAML file for testing"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("")
            temp_file = f.name
        
        yield Path(temp_file)
        
        # Cleanup
        try:
            os.unlink(temp_file)
        except OSError:
            pass
    
    def test_project_store_creation(self, temp_yaml_file):
        """Test creating a project store with existing data"""
        store = ProjectStore(temp_yaml_file)
        
        projects = store.list_projects()
        assert len(projects) == 2
        
        # Check first project
        project1 = next(p for p in projects if p.config.id == "test-project-1")
        assert project1.config.name == "Test Project 1"
        assert project1.config.working_dir == "/path/to/project1"
        assert project1.config.command == "python"
        assert project1.config.args == ["app.py"]
        assert project1.config.instances == 1
        assert project1.config.description == "First test project"
        
        # Check second project
        project2 = next(p for p in projects if p.config.id == "test-project-2")
        assert project2.config.name == "Test Project 2"
        assert project2.config.working_dir == "/path/to/project2"
        assert project2.config.command == "node"
        assert project2.config.args == ["server.js"]
        assert project2.config.instances == 2
        assert project2.config.description == "Second test project"
    
    def test_project_store_empty_file(self, empty_yaml_file):
        """Test creating a project store with empty file"""
        store = ProjectStore(empty_yaml_file)
        
        projects = store.list_projects()
        assert len(projects) == 0
    
    def test_project_store_nonexistent_file(self):
        """Test creating a project store with nonexistent file"""
        temp_dir = tempfile.mkdtemp()
        yaml_path = Path(temp_dir) / "nonexistent.yaml"
        
        store = ProjectStore(yaml_path)
        
        projects = store.list_projects()
        assert len(projects) == 0
        
        # Cleanup
        try:
            os.rmdir(temp_dir)
        except OSError:
            pass
    
    def test_get_project(self, temp_yaml_file):
        """Test getting a specific project"""
        store = ProjectStore(temp_yaml_file)
        
        project = store.get_project("test-project-1")
        assert project is not None
        assert project.config.id == "test-project-1"
        assert project.config.name == "Test Project 1"
        
        # Test getting non-existent project
        project = store.get_project("nonexistent")
        assert project is None
    
    def test_upsert_project_new(self, temp_yaml_file):
        """Test adding a new project"""
        store = ProjectStore(temp_yaml_file)
        
        config = ProjectConfig(
            id="new-project",
            name="New Project",
            working_dir="/path/to/new",
            command="python",
            args=["new_app.py"],
            instances=3,
            description="A new test project"
        )
        
        project = store.upsert_project(config)
        
        assert project.config.id == "new-project"
        assert project.config.name == "New Project"
        assert project.config.working_dir == "/path/to/new"
        assert project.config.command == "python"
        assert project.config.args == ["new_app.py"]
        assert project.config.instances == 3
        assert project.config.description == "A new test project"
        
        # Verify it's in the list
        projects = store.list_projects()
        assert len(projects) == 3
        
        new_project = next(p for p in projects if p.config.id == "new-project")
        assert new_project.config.name == "New Project"
    
    def test_upsert_project_existing(self, temp_yaml_file):
        """Test updating an existing project"""
        store = ProjectStore(temp_yaml_file)
        
        # Get existing project
        existing_project = store.get_project("test-project-1")
        assert existing_project is not None
        
        # Update the project
        updated_config = ProjectConfig(
            id="test-project-1",
            name="Updated Test Project 1",
            working_dir="/updated/path",
            command="python3",
            args=["updated_app.py"],
            instances=5,
            description="Updated description"
        )
        
        updated_project = store.upsert_project(updated_config)
        
        assert updated_project.config.id == "test-project-1"
        assert updated_project.config.name == "Updated Test Project 1"
        assert updated_project.config.working_dir == "/updated/path"
        assert updated_project.config.command == "python3"
        assert updated_project.config.args == ["updated_app.py"]
        assert updated_project.config.instances == 5
        assert updated_project.config.description == "Updated description"
        
        # Verify the update
        projects = store.list_projects()
        assert len(projects) == 2  # Should still be 2 projects
        
        updated = next(p for p in projects if p.config.id == "test-project-1")
        assert updated.config.name == "Updated Test Project 1"
    
    def test_delete_project(self, temp_yaml_file):
        """Test deleting a project"""
        store = ProjectStore(temp_yaml_file)
        
        # Verify project exists
        project = store.get_project("test-project-1")
        assert project is not None
        
        # Delete the project
        deleted = store.delete_project("test-project-1")
        assert deleted is True
        
        # Verify project is gone
        project = store.get_project("test-project-1")
        assert project is None
        
        # Verify list is updated
        projects = store.list_projects()
        assert len(projects) == 1
        assert projects[0].config.id == "test-project-2"
        
        # Test deleting non-existent project
        deleted = store.delete_project("nonexistent")
        assert deleted is False
    
    def test_project_store_persistence(self, temp_yaml_file):
        """Test that changes are persisted to disk"""
        store = ProjectStore(temp_yaml_file)
        
        # Add a new project
        config = ProjectConfig(
            id="persistent-project",
            name="Persistent Project",
            working_dir="/persistent/path",
            command="python",
            args=["persistent.py"],
            instances=1
        )
        
        store.upsert_project(config)
        
        # Create a new store instance with the same file
        new_store = ProjectStore(temp_yaml_file)
        
        # Verify the project is still there
        project = new_store.get_project("persistent-project")
        assert project is not None
        assert project.config.name == "Persistent Project"
        
        projects = new_store.list_projects()
        assert len(projects) == 3  # Original 2 + new 1
    
    def test_project_store_invalid_yaml(self):
        """Test handling of invalid YAML file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
invalid: yaml: content: here
  - this: is: not: valid: yaml
""")
            temp_file = f.name
        
        try:
            store = ProjectStore(Path(temp_file))
            
            # Should handle invalid YAML gracefully
            projects = store.list_projects()
            assert len(projects) == 0
        finally:
            # Cleanup
            try:
                os.unlink(temp_file)
            except OSError:
                pass
    
    def test_project_store_missing_required_fields(self):
        """Test handling of projects with missing required fields"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
projects:
  - id: "valid-project"
    name: "Valid Project"
    working_dir: "/valid/path"
    command: "python"
    
  - id: "invalid-project"
    name: "Invalid Project"
    # Missing working_dir and command
    
  - id: "another-valid"
    name: "Another Valid"
    working_dir: "/another/path"
    command: "node"
""")
            temp_file = f.name
        
        try:
            store = ProjectStore(Path(temp_file))
            
            # Should only load valid projects
            projects = store.list_projects()
            assert len(projects) == 2  # Only valid projects
            
            valid_ids = [p.config.id for p in projects]
            assert "valid-project" in valid_ids
            assert "another-valid" in valid_ids
            assert "invalid-project" not in valid_ids
        finally:
            # Cleanup
            try:
                os.unlink(temp_file)
            except OSError:
                pass 