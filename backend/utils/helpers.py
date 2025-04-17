# helpers.py
# Created: 2025-04-06 16:00:50
# Edited by: King
# Description: Utility functions like name normalization, fuzzy matching, etc.

import re
from fuzzywuzzy import fuzz
from sqlalchemy.orm import sessionmaker
from backend.db import get_engine
from backend.config import settings
import json


def normalize_name(name):
    """Lowercase and strip whitespace."""
    return name.strip().lower()

def calculate_name_similarity(name1, name2):
    """Calculate fuzzy matching score between two names."""
    name1_norm = normalize_name(name1)
    name2_norm = normalize_name(name2)
    return fuzz.ratio(name1_norm, name2_norm)

def calculate_match_score(individual1, individual2):
    """
    Calculate a match score based on name similarity and other factors.
    For now, we use name similarity; later you can add birth date proximity, shared locations, etc.
    """
    score = 0
    if hasattr(individual1, 'name') and hasattr(individual2, 'name'):
        score += calculate_name_similarity(individual1.name, individual2.name)
    return score

# Additional utility functions can be added here.

# Legacy DB connection function updated to use our central engine.
def get_db_connection():
    engine = get_engine()
    Session = sessionmaker(bind=engine)
    return Session()

def normalize_location_name(name):
    return re.sub(r'\W+', '_', name.strip().lower())

def print_json(obj):
    print(json.dumps(obj, indent=2, ensure_ascii=False))

def normalize_confidence_score(value):
    """Convert string/numeric confidence values to a float."""
    mapping = {
        "very high": 0.95,
        "high": 0.85,
        "medium": 0.5,
        "low": 0.25,
        "very low": 0.1,
        "unknown": 0.0,
        None: 0.0,
    }
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return mapping.get(value.strip().lower(), 0.0)
    return 0.0
