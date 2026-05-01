import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import init_db, engine
from app.db.base import Base

# Import all models so they register with Base.metadata
from app.models.raw_article import RawArticle
from app.models.processed_article import ProcessedArticle
from app.models.quiz import Quiz

print("Creating database tables...")
init_db()
print("Done. Tables created:")

from sqlalchemy import inspect
inspector = inspect(engine)
for table in inspector.get_table_names():
    columns = [col["name"] for col in inspector.get_columns(table)]
    print(f"  - {table}: {', '.join(columns)}")
