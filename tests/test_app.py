"""
Tests for the Mergington High School Activities API.
"""

import copy
import pytest
from fastapi.testclient import TestClient

import src.app as app_module
from src.app import app

client = TestClient(app)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def reset_participants():
    """Restore each activity's participant list to its original state after every test."""
    original = {
        name: list(details["participants"])
        for name, details in app_module.activities.items()
        if isinstance(details, dict) and "participants" in details
    }
    yield
    for name, participants in original.items():
        app_module.activities[name]["participants"] = participants


# ---------------------------------------------------------------------------
# GET /activities
# ---------------------------------------------------------------------------

class TestGetActivities:
    def test_returns_200(self):
        response = client.get("/activities")
        assert response.status_code == 200

    def test_returns_dict(self):
        response = client.get("/activities")
        data = response.json()
        assert isinstance(data, dict)

    def test_known_activity_present(self):
        response = client.get("/activities")
        data = response.json()
        assert "Soccer Team" in data

    def test_activity_has_required_fields(self):
        response = client.get("/activities")
        data = response.json()
        activity = data["Soccer Team"]
        assert "description" in activity
        assert "schedule" in activity
        assert "max_participants" in activity
        assert "participants" in activity


# ---------------------------------------------------------------------------
# POST /activities/{activity_name}/signup
# ---------------------------------------------------------------------------

class TestSignup:
    def test_successful_signup(self):
        response = client.post(
            "/activities/Soccer Team/signup",
            params={"email": "newstudent@mergington.edu"},
        )
        assert response.status_code == 200
        assert "message" in response.json()

    def test_signup_adds_participant(self):
        email = "newstudent@mergington.edu"
        client.post("/activities/Soccer Team/signup", params={"email": email})
        participants = client.get("/activities").json()["Soccer Team"]["participants"]
        assert email in participants

    def test_signup_unknown_activity_returns_404(self):
        response = client.post(
            "/activities/Nonexistent Club/signup",
            params={"email": "student@mergington.edu"},
        )
        assert response.status_code == 404

    def test_signup_duplicate_returns_400(self):
        email = "duplicate@mergington.edu"
        client.post("/activities/Soccer Team/signup", params={"email": email})
        response = client.post("/activities/Soccer Team/signup", params={"email": email})
        assert response.status_code == 400

    def test_signup_response_contains_email_and_activity(self):
        email = "check@mergington.edu"
        response = client.post("/activities/Soccer Team/signup", params={"email": email})
        message = response.json()["message"]
        assert email in message
        assert "Soccer Team" in message


# ---------------------------------------------------------------------------
# DELETE /activities/{activity_name}/unregister
# ---------------------------------------------------------------------------

class TestUnregister:
    def test_successful_unregister(self):
        # First sign up so we have someone to remove
        email = "tounregister@mergington.edu"
        client.post("/activities/Soccer Team/signup", params={"email": email})

        response = client.delete(
            "/activities/Soccer Team/unregister",
            params={"email": email},
        )
        assert response.status_code == 200
        assert "message" in response.json()

    def test_unregister_removes_participant(self):
        email = "tounregister@mergington.edu"
        client.post("/activities/Soccer Team/signup", params={"email": email})
        client.delete("/activities/Soccer Team/unregister", params={"email": email})

        participants = client.get("/activities").json()["Soccer Team"]["participants"]
        assert email not in participants

    def test_unregister_unknown_activity_returns_404(self):
        response = client.delete(
            "/activities/Nonexistent Club/unregister",
            params={"email": "student@mergington.edu"},
        )
        assert response.status_code == 404

    def test_unregister_not_signed_up_returns_400(self):
        response = client.delete(
            "/activities/Soccer Team/unregister",
            params={"email": "notregistered@mergington.edu"},
        )
        assert response.status_code == 400

    def test_unregister_response_contains_email_and_activity(self):
        email = "tounregister@mergington.edu"
        client.post("/activities/Soccer Team/signup", params={"email": email})
        response = client.delete(
            "/activities/Soccer Team/unregister", params={"email": email}
        )
        message = response.json()["message"]
        assert email in message
        assert "Soccer Team" in message


# ---------------------------------------------------------------------------
# GET / redirect
# ---------------------------------------------------------------------------

class TestRootRedirect:
    def test_root_redirects(self):
        response = client.get("/", follow_redirects=False)
        assert response.status_code in (301, 302, 307, 308)
        assert "/static/index.html" in response.headers["location"]
