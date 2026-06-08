import pytest
from copy import deepcopy
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Provide a TestClient instance for API testing"""
    return TestClient(app)


@pytest.fixture
def fresh_activities():
    """Provide a fresh copy of activities data to avoid test interference"""
    return deepcopy(activities)


@pytest.fixture(autouse=True)
def reset_activities(fresh_activities):
    """Reset the activities data before each test to ensure isolation"""
    global activities
    # Clear the current activities
    activities.clear()
    # Copy fresh data back into activities
    activities.update(fresh_activities)
    yield
    # Cleanup after test
    activities.clear()
    activities.update(fresh_activities)
