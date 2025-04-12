
# File: config.py
# Created: 2025-04-06 16:00:50
# Edited by: King
# Last Edited: 2025-04-06 16:00:50
# Description: Configuration settings; use environment variables or defaults.

# config.py
# File: config.py
# Description: Configuration settings using environment variables or fallbacks

import os
from dotenv import load_dotenv

# Load .env file
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

# Core DB config
DB_NAME = os.getenv('DB_NAME', 'genealogy_db')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = int(os.getenv('DB_PORT', 5432))

# Build full config dict
DB_CONFIG = {
    'dbname': DB_NAME,
    'user': DB_USER,
    'password': DB_PASSWORD,
    'host': DB_HOST,
    'port': DB_PORT
}

# Construct SQLAlchemy-compatible URI
DATABASE_URI = f"postgresql+psycopg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Optional app settings
PORT = int(os.getenv("PORT", 5050))
DEBUG = os.getenv("DEBUG", "True").lower() == "true"
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "AIzaSyD-qMCG2R5zrgpe1IEqQGJCvL4Y0U2Ryt4")

# Debug printout
print("Loaded DB config:", DB_CONFIG)
