from fastapi.testclient import TestClient

from src import app as app_module


client = TestClient(app_module.app)


def test_root_redirects_to_index():
    # Arrange
    expected_location = "/static/index.html"

    # Act
    response = client.get("/", follow_redirects=False)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == expected_location


def test_get_activities_returns_available_activities():
    # Arrange
    expected_activities = app_module.activities.copy()

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json() == expected_activities


def test_signup_adds_participant(monkeypatch):
    # Arrange
    activity_name = "Chess Club"
    email = "student@mergington.edu"
    test_activities = {
        activity_name: {
            "description": "Learn to play chess",
            "schedule": "Fridays",
            "max_participants": 12,
            "participants": [],
        }
    }
    monkeypatch.setattr(app_module, "activities", test_activities)

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {
        "message": f"Signed up {email} for {activity_name}"
    }
    assert test_activities[activity_name]["participants"] == [email]


def test_signup_for_unknown_activity_returns_not_found():
    # Arrange
    activity_name = "Unknown Club"
    email = "student@mergington.edu"

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}
