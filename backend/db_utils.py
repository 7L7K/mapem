from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.config import DB_CONFIG
from backend.models import Base

def get_db_connection():
    url = f"postgresql://{DB_CONFIG['user']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['dbname']}"
    engine = create_engine(url)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()
