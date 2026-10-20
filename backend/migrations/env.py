from alembic import context
from app.db import Base, engine
from app import models
config=context.config
target_metadata=Base.metadata
if context.is_offline_mode():
    from app.config import settings
    from app.db import normalize_url
    context.configure(url=normalize_url(settings.database_url),target_metadata=target_metadata,literal_binds=True,compare_type=True)
    with context.begin_transaction(): context.run_migrations()
else:
    with engine.connect() as connection:
        context.configure(connection=connection,target_metadata=target_metadata,compare_type=True)
        with context.begin_transaction(): context.run_migrations()
