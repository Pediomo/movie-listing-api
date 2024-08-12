from __future__ import with_statement
import sys
import os
from alembic import context
from sqlalchemy import engine_from_config, pool
from app.database import Base, engine
from app.models import User, Movie, Rating, Comment  # Ensure your models are imported

# Set the path to the app module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

config = context.config
config.set_main_option('sqlalchemy.url', str(engine.url))

def run_migrations_offline():
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=Base.metadata, literal_binds=True, dialect_opts={"paramstyle": "named"})

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(config.get_section(config.config_ini_section), prefix='sqlalchemy.', poolclass=pool.NullPool)

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=Base.metadata)

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
