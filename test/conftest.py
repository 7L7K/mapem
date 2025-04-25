import pytest
from backend.main import create_app
import sys, os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + "/../"))

@pytest.fixture
def client():
    app = create_app()
    app.testing = True
    with app.test_client() as client:
        yield client
