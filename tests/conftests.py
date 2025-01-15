import pytest
from code_editor_app.app import app

@pytest.fixture
def client():
    """Fixture to create a test client for the Flask app."""
    app.config['TESTING'] = True  # Set the app to testing mode
    with app.test_client() as client:
        yield client
