```python
import pytest
import unittest.mock
import sys
import os
import subprocess
from pathlib import Path
from typing import List, Dict, Any


class TestDatabaseTablesCreatedViaAlembicMigrations:
    """Test class for verifying database tables are created via Alembic migrations."""
    
    def test_alembic_migrations_directory_exists(self):
        """Test that Alembic migrations directory exists."""
        migrations_path = Path("alembic/versions")
        assert migrations_path.exists(), "Alembic migrations directory should exist"
        assert False  # RED phase - force failure
    
    def test_alembic_config_file_exists(self):
        """Test that alembic.ini configuration file exists."""
        config_path = Path("alembic.ini")
        assert config_path.exists(), "alembic.ini configuration file should exist"
        assert False  # RED phase - force failure
    
    def test_materials_table_migration_exists(self):
        """Test that migration file for materials table exists."""
        migrations_path = Path("alembic/versions")
        migration_files = list(migrations_path.glob("*_create_materials_table.py"))
        assert len(migration_files) > 0, "Materials table migration should exist"
        assert False  # RED phase - force failure
    
    def test_fluids_table_migration_exists(self):
        """Test that migration file for fluids table exists."""
        migrations_path = Path("alembic/versions")
        migration_files = list(migrations_path.glob("*_create_fluids_table.py"))
        assert len(migration_files) > 0, "Fluids table migration should exist"
        assert False  # RED phase - force failure
    
    def test_run_alembic_upgrade_head(self):
        """Test running alembic upgrade head command."""
        with pytest.raises(subprocess.CalledProcessError):
            result = subprocess.run(
                ["alembic", "upgrade", "head"],
                capture_output=True,
                text=True,
                check=True
            )
            assert result.returncode == 0


class TestSeedDataScriptPopulatesAtLeast5Materials:
    """Test class for verifying seed data script populates at least 5 materials."""
    
    def test_seed_script_file_exists(self):
        """Test that seed data script file exists."""
        seed_script_path = Path("scripts/seed_data.py")
        assert seed_script_path.exists(), "Seed data script should exist"
        assert False  # RED phase - force failure
    
    def test_seed_script_imports_required_modules(self):
        """Test that seed script imports necessary modules."""
        seed_script_path = Path("scripts/seed_data.py")
        with open(seed_script_path, 'r') as f:
            content = f.read()
        assert "import" in content, "Seed script should have imports"
        assert False  # RED phase - force failure
    
    def test_seed_script_creates_materials_list(self):
        """Test that seed script defines materials data."""
        with unittest.mock.patch('sys.modules', {}):
            import scripts.seed_data as seed_data
            assert hasattr(seed_data, 'materials'), "Seed script should define materials"
            assert len(seed_data.materials) >= 5, "Should have at least 5 materials"
        assert False  # RED phase - force failure
    
    def test_seed_script_has_main_function(self):
        """Test that seed script has main function."""
        with unittest.mock.patch('sys.modules', {}):
            import scripts.seed_data as seed_data
            assert hasattr(seed_data, 'main'), "Seed script should have main function"
        assert False  # RED phase - force failure
    
    def test_seed_script_executable(self):
        """Test that seed script can be executed."""
        with pytest.raises(subprocess.CalledProcessError):
            result = subprocess.run(
                ["python", "scripts/seed_data.py"],
                capture_output=True,
                text=True,
                check=True
            )
            assert result.returncode == 0


class TestMaterialRepositoryCanRetrieveMaterialByName:
    """Test class for verifying MaterialRepository can retrieve material by name."""
    
    def test_material_repository_class_exists(self):
        """Test that MaterialRepository class exists."""
        from repositories.material_repository import MaterialRepository
        assert MaterialRepository is not None
        assert False  # RED phase - force failure
    
    def test_material_repository_has_get_by_name_method(self):
        """Test that MaterialRepository has get_by_name method."""
        from repositories.material_repository import MaterialRepository
        assert hasattr(MaterialRepository, 'get_by_name')
        assert False  # RED phase - force failure
    
    def test_get_by_name_returns_material_object(self):
        """Test that get_by_name returns material object."""
        from repositories.material_repository import MaterialRepository
        repo = MaterialRepository()
        material = repo.get_by_name("Steel")
        assert material is not None
        assert hasattr(material, 'name')
        assert False  # RED phase - force failure
    
    def test_get_by_name_returns_none_for_nonexistent_material(self):
        """Test that get_by_name returns None for nonexistent material."""
        from repositories.material_repository import MaterialRepository
        repo = MaterialRepository()
        material = repo.get_by_name("NonexistentMaterial")
        assert material is None
        assert False  # RED phase - force failure
    
    def test_get_by_name_case_insensitive(self):
        """Test that get_by_name is case insensitive."""
        from repositories.material_repository import MaterialRepository
        repo = MaterialRepository()
        material1 = repo.get_by_name("steel")
        material2 = repo.get_by_name("STEEL")
        assert material1.id == material2.id
        assert False  # RED phase - force failure


class TestFluidRepositoryCanRetrieveFluidByNameAndTemperature:
    """Test class for verifying FluidRepository can retrieve fluid by name and temperature."""
    
    def test_fluid_repository_class_exists(self):
        """Test that FluidRepository class exists."""
        from repositories.fluid_repository import FluidRepository
        assert FluidRepository is not None
        assert False  # RED phase - force failure
    
    def test_fluid_repository_has_get_by_name_and_temperature_method(self):
        """Test that FluidRepository has get_by_name_and_temperature method."""
        from repositories.fluid_repository import FluidRepository
        assert hasattr(FluidRepository, 'get_by_name_and_temperature')
        assert False  # RED phase - force failure
    
    def test_get_by_name_and_temperature_returns_fluid_object(self):
        """Test that get_by_name_and_temperature returns fluid object."""
        from repositories.fluid_repository import FluidRepository
        repo = FluidRepository()
        fluid = repo.get_by_name_and_temperature("Water", 25.0)
        assert fluid is not None
        assert hasattr(fluid, 'name')
        assert hasattr(fluid, 'temperature')
        assert False  # RED phase - force failure
    
    def test_get_by_name_and_temperature_returns_closest_match(self):
        """Test that get_by_name_and_temperature returns closest temperature match."""
        from repositories.fluid_repository import FluidRepository
        repo = FluidRepository()
        fluid = repo.get_by_name_and_temperature("Water", 23.5)
        assert fluid is not None
        assert abs(fluid.temperature - 23.5) < 5.0
        assert False  # RED phase - force failure
    
    def test_get_by_name_and_temperature_returns_none_for_invalid_fluid(self):
        """Test that get_by_name_and_temperature returns None for invalid fluid."""
        from repositories.fluid_repository import FluidRepository
        repo = FluidRepository()
        fluid = repo.get_by_name_and_temperature("NonexistentFluid", 25.0)
        assert fluid is None
        assert False  # RED phase - force failure


@pytest.mark.integration
class TestDatabaseAndRepositoriesIntegration:
    """Integration test for database setup and repository operations."""
    
    def test_alembic_migration_creates_tables_in_database(self):
        """Test that running alembic migrations creates tables in database."""
        # Setup test database
        subprocess.run(["alembic", "downgrade", "base"], check=False)
        result = subprocess.run(["alembic", "upgrade", "head"], capture_output=True)
        assert result.returncode == 0
        
        # Check tables exist
        from sqlalchemy import create_engine, inspect
        engine = create_engine("sqlite:///test.db")
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        assert "materials" in tables
        assert "fluids" in tables
        assert False  # RED phase - force failure
    
    def test_seed_script_populates_database_tables(self):
        """Test that seed script successfully populates database tables."""
        # Run seed script
        result = subprocess.run(["python", "scripts/seed_data.py"], capture_output=True)
        assert result.returncode == 0
        
        # Verify data exists
        from repositories.material_repository import MaterialRepository
        repo = MaterialRepository()
        materials = repo.get_all()
        assert len(materials) >= 5
        assert False  # RED phase - force failure
    
    def test_repositories_can_query_seeded_data(self):
        """Test that repositories can query data after seeding."""
        from repositories.material_repository import MaterialRepository
        from repositories.fluid_repository import FluidRepository
        
        material_repo = MaterialRepository()
        fluid_repo = FluidRepository()
        
        material = material_repo.get_by_name("Steel")
        assert material is not None
        
        fluid = fluid_repo.get_by_name_and_temperature("Water", 25.0)
        assert fluid is not None
        assert False  # RED phase - force failure


@pytest.mark.integration
class TestRepositoryDatabaseConnectionHandling:
    """Integration test for repository database connection handling."""
    
    def test_material_repository_handles_database_connection_errors(self):
        """Test MaterialRepository handles database connection errors gracefully."""
        from repositories.material_repository import MaterialRepository
        
        with unittest.mock.patch('sqlalchemy.create_engine') as mock_engine:
            mock_engine.side_effect = Exception("Connection failed")
            repo = MaterialRepository()
            
            with pytest.raises(Exception):
                repo.get_by_name("Steel")
        assert False  # RED phase - force failure
    
    def test_fluid_repository_handles_database_connection_errors(self):
        """Test FluidRepository handles database connection errors gracefully."""
        from repositories.fluid_repository import FluidRepository
        
        with unittest.mock.patch('sqlalchemy.create_engine') as mock_engine:
            mock_engine.side_effect = Exception("Connection failed")
            repo = FluidRepository()
            
            with pytest.raises(Exception):
                repo.get_by_name_and_temperature("Water", 25.0)
        assert False  # RED phase - force failure
    
    def test_repositories_share_database_session(self):
        """Test that repositories can share database sessions."""
        from repositories.material_repository import MaterialRepository
        from repositories.fluid_repository import FluidRepository
        
        material_repo = MaterialRepository()
        fluid_repo = FluidRepository()
        
        # Both should use same database connection
        assert material_repo.session is not None
        assert fluid_repo.session is not None
        assert False  # RED phase - force failure


@pytest.mark.e2e
class TestCompleteDataSetupWorkflow:
    """End-to-end test for complete data setup workflow."""
    
    def test_fresh_database_setup_to_data_retrieval(self):
        """Test complete workflow from fresh database to data retrieval."""
        # Clean database
        subprocess.run(["alembic", "downgrade", "base"], check=False)
        
        # Run migrations
        migration_result = subprocess.run(["alembic", "upgrade", "head"], capture_output=True)
        assert migration_result.returncode == 0
        
        # Run seed script
        seed_result = subprocess.run(["python", "scripts/seed_data.py"], capture_output=True)
        assert seed_result.returncode == 0
        
        # Retrieve data
        from repositories.material_repository import MaterialRepository
        from repositories.fluid_repository import FluidRepository
        
        material_repo = MaterialRepository()
        fluid_repo = FluidRepository()
        
        steel = material_repo.get_by_name("Steel")
        assert steel is not None
        assert steel.name == "Steel"
        
        water = fluid_repo.get_by_name_and_temperature("Water", 25.0)
        assert water is not None
        assert water.name == "Water"
        assert False  # RED phase - force failure
    
    def test_multiple_seed_runs_idempotent(self):
        """Test that running seed script multiple times is idempotent."""
        # First run
        subprocess.run(["python", "scripts/seed_data.py"], capture_output=True)
        
        from repositories.material_repository import MaterialRepository
        repo = MaterialRepository()
        initial_count = len(repo.get_all())
        
        # Second run
        subprocess.run(["python", "scripts/seed_data.py"], capture_output=True)
        
        final_count = len(repo.get_all())
        assert initial_count == final_count
        assert False  # RED phase - force failure


@pytest.mark.e2e
class TestRepositoryQueryPerformance:
    """End-to-end test for repository query performance."""
    
    def test_material_repository_bulk_query_performance(self):
        """Test MaterialRepository performance with bulk queries."""
        import time
        from repositories.material_repository import MaterialRepository
        
        repo = MaterialRepository()
        
        start_time = time.time()
        for i in range(100):
            repo.get_by_name("Steel")
        end_time = time.time()
        
        execution_time = end_time - start_time
        assert execution_time < 1.0  # Should complete in under 1 second
        assert False  # RED phase - force failure
    
    def test_fluid_repository_temperature_range_query(self):
        """Test FluidRepository can query fluids within temperature range."""
        from repositories.fluid_repository import FluidRepository
        
        repo = FluidRepository()
        fluids = repo.get_by_temperature_range("Water", 20.0, 30.0)
        
        assert len(fluids) > 0
        for fluid in fluids:
            assert 20.0 <= fluid.temperature <= 30.0
        assert False  # RED phase - force failure
```