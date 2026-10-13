from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from src import app as app_module


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setattr(app_module, "activities", deepcopy(app_module.activities))
    return TestClient(app_module.app)


def test_root_redirects_to_index(client: TestClient) -> None:
    # Arrange
    expected_location = "/static/index.html"

    # Act
    response = client.get("/", follow_redirects=False)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == expected_location


def test_static_index_is_served(client: TestClient) -> None:
    # Arrange
    expected_heading = "<h1>Mergington High School</h1>"

    # Act
    response = client.get("/static/index.html")

    # Assert
    assert response.status_code == 200
    assert expected_heading in response.text


def test_get_activities_returns_available_activities(client: TestClient) -> None:
    # Arrange
    expected_activity_names = {"Chess Club", "Programming Class", "Gym Class"}
    expected_chess_participants = [
        "michael@mergington.edu",
        "daniel@mergington.edu",
    ]

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    activities = response.json()
    assert set(activities) == expected_activity_names
    assert activities["Chess Club"]["participants"] == expected_chess_participants


def test_signup_adds_participant(client: TestClient) -> None:
    # Arrange
    activity_name = "Chess Club"
    email = "student@mergington.edu"

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )
    activities = client.get("/activities").json()

    # Assert
    assert response.status_code == 200
    assert response.json() == {
        "message": f"Signed up {email} for {activity_name}"
    }
    assert email in activities[activity_name]["participants"]


def test_signup_rejects_duplicate_participant(client: TestClient) -> None:
    # Arrange
    activity_name = "Chess Club"
    email = "student@mergington.edu"
    signup_url = f"/activities/{activity_name}/signup"
    client.post(signup_url, params={"email": email})

    # Act
    response = client.post(signup_url, params={"email": email})
    participants = client.get("/activities").json()[activity_name]["participants"]

    # Assert
    assert response.status_code == 409
    assert response.json() == {
        "detail": "Student is already signed up for this activity"
    }
    assert participants.count(email) == 1


def test_signup_for_unknown_activity_returns_not_found(client: TestClient) -> None:
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


def test_signup_without_email_returns_validation_error(client: TestClient) -> None:
    # Arrange
    activity_name = "Chess Club"

    # Act
    response = client.post(f"/activities/{activity_name}/signup")

    # Assert
    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["query", "email"]
    assert response.json()["detail"][0]["type"] == "missing"
