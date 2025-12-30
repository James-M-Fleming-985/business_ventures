```python
# models.py
from sqlalchemy import Column, Integer, String, Float, ForeignKey, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

Base = declarative_base()

class Material(Base):
    __tablename__ = 'materials'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False, unique=True)
    type = Column(String(50), nullable=False)
    thermal_conductivity = Column(Float, nullable=False)
    density = Column(Float, nullable=False)
    specific_heat_capacity = Column(Float, nullable=False)
    
    def __repr__(self):
        return f"<Material(name='{self.name}', type='{self.type}')>"

class Fluid(Base):
    __tablename__ = 'fluids'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    temperature = Column(Float, nullable=False)
    pressure = Column(Float, nullable=False)
    density = Column(Float, nullable=False)
    viscosity = Column(Float, nullable=False)
    specific_heat_capacity = Column(Float, nullable=False)
    thermal_conductivity = Column(Float, nullable=False)
    
    def __repr__(self):
        return f"<Fluid(name='{self.name}', temperature={self.temperature})>"

# database.py
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from models import Base
import os

DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./materials.db')

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@contextmanager
def get_db():
    """Provide a transactional scope around a series of operations."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initialize the database tables."""
    Base.metadata.create_all(bind=engine)

# repositories.py
from typing import Optional, List
from sqlalchemy.orm import Session
from models import Material, Fluid
from database import get_db

class MaterialRepository:
    """Repository for managing Material entities."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_name(self, name: str) -> Optional[Material]:
        """
        Retrieve a material by its name.
        
        Args:
            name: The name of the material
            
        Returns:
            Material object if found, None otherwise
        """
        return self.db.query(Material).filter(Material.name == name).first()
    
    def get_all(self) -> List[Material]:
        """
        Retrieve all materials.
        
        Returns:
            List of all Material objects
        """
        return self.db.query(Material).all()
    
    def create(self, material: Material) -> Material:
        """
        Create a new material.
        
        Args:
            material: Material object to create
            
        Returns:
            Created Material object
        """
        self.db.add(material)
        self.db.commit()
        self.db.refresh(material)
        return material

class FluidRepository:
    """Repository for managing Fluid entities."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_name_and_temperature(self, name: str, temperature: float) -> Optional[Fluid]:
        """
        Retrieve a fluid by its name and temperature.
        
        Args:
            name: The name of the fluid
            temperature: The temperature of the fluid
            
        Returns:
            Fluid object if found, None otherwise
        """
        return self.db.query(Fluid).filter(
            Fluid.name == name,
            Fluid.temperature == temperature
        ).first()
    
    def get_all(self) -> List[Fluid]:
        """
        Retrieve all fluids.
        
        Returns:
            List of all Fluid objects
        """
        return self.db.query(Fluid).all()
    
    def create(self, fluid: Fluid) -> Fluid:
        """
        Create a new fluid.
        
        Args:
            fluid: Fluid object to create
            
        Returns:
            Created Fluid object
        """
        self.db.add(fluid)
        self.db.commit()
        self.db.refresh(fluid)
        return fluid

# seed_data.py
from database import engine, SessionLocal, init_db
from models import Material, Fluid
from repositories import MaterialRepository, FluidRepository

def seed_materials():
    """Seed the database with initial material data."""
    init_db()
    
    db = SessionLocal()
    material_repo = MaterialRepository(db)
    fluid_repo = FluidRepository(db)
    
    # Clear existing data
    db.query(Material).delete()
    db.query(Fluid).delete()
    db.commit()
    
    # Materials data
    materials_data = [
        {
            'name': 'Copper',
            'type': 'metal',
            'thermal_conductivity': 401.0,
            'density': 8960.0,
            'specific_heat_capacity': 385.0
        },
        {
            'name': 'Aluminum',
            'type': 'metal',
            'thermal_conductivity': 237.0,
            'density': 2700.0,
            'specific_heat_capacity': 897.0
        },
        {
            'name': 'Steel',
            'type': 'metal',
            'thermal_conductivity': 50.2,
            'density': 7850.0,
            'specific_heat_capacity': 466.0
        },
        {
            'name': 'Glass Wool',
            'type': 'insulation',
            'thermal_conductivity': 0.04,
            'density': 20.0,
            'specific_heat_capacity': 840.0
        },
        {
            'name': 'Polyurethane Foam',
            'type': 'insulation',
            'thermal_conductivity': 0.026,
            'density': 30.0,
            'specific_heat_capacity': 1400.0
        },
        {
            'name': 'Concrete',
            'type': 'building',
            'thermal_conductivity': 1.7,
            'density': 2400.0,
            'specific_heat_capacity': 880.0
        }
    ]
    
    # Fluids data
    fluids_data = [
        {
            'name': 'Water',
            'temperature': 20.0,
            'pressure': 101325.0,
            'density': 998.2,
            'viscosity': 0.001002,
            'specific_heat_capacity': 4182.0,
            'thermal_conductivity': 0.598
        },
        {
            'name': 'Water',
            'temperature': 80.0,
            'pressure': 101325.0,
            'density': 971.8,
            'viscosity': 0.000355,
            'specific_heat_capacity': 4196.0,
            'thermal_conductivity': 0.670
        },
        {
            'name': 'Air',
            'temperature': 20.0,
            'pressure': 101325.0,
            'density': 1.204,
            'viscosity': 0.00001813,
            'specific_heat_capacity': 1005.0,
            'thermal_conductivity': 0.0257
        },
        {
            'name': 'Engine Oil',
            'temperature': 40.0,
            'pressure': 101325.0,
            'density': 876.0,
            'viscosity': 0.212,
            'specific_heat_capacity': 1880.0,
            'thermal_conductivity': 0.144
        },
        {
            'name': 'Glycol',
            'temperature': 25.0,
            'pressure': 101325.0,
            'density': 1113.0,
            'viscosity': 0.0161,
            'specific_heat_capacity': 2400.0,
            'thermal_conductivity': 0.286
        }
    ]
    
    # Insert materials
    for material_data in materials_data:
        material = Material(**material_data)
        material_repo.create(material)
    
    # Insert fluids
    for fluid_data in fluids_data:
        fluid = Fluid(**fluid_data)
        fluid_repo.create(fluid)
    
    db.close()
    print("Seed data inserted successfully!")

if __name__ == "__main__":
    seed_materials()

# alembic.ini
[alembic]
script_location = alembic
prepend_sys_path = .
version_path_separator = os
sqlalchemy.url = sqlite:///./materials.db

[alembic:exclude]
tables = 

[post_write_hooks]

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S

# alembic/env.py
from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from models import Base

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

# alembic/versions/001_create_materials_and_fluids_tables.py
"""create materials and fluids tables

Revision ID: 001
Revises: 
Create Date: 2023-12-29 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Create materials table
    op.create_table('materials',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('type', sa.String(50), nullable=False),
        sa.Column('thermal_conductivity', sa.Float(), nullable=False),
        sa.Column('density', sa.Float(), nullable=False),
        sa.Column('specific_heat_capacity', sa.Float(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    
    # Create fluids table
    op.create_table('fluids',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('temperature', sa.Float(), nullable=False),
        sa.Column('pressure', sa.Float(), nullable=False),
        sa.Column('density', sa.Float(), nullable=False),
        sa.Column('viscosity', sa.Float(), nullable=False),
        sa.Column('specific_heat_capacity', sa.Float(), nullable=False),
        sa.Column('thermal_conductivity', sa.Float(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade():
    op.drop_table('fluids')
    op.drop_table('materials')
```