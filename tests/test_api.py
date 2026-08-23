import pytest
from fastapi.testclient import TestClient
from core.gateway import app

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Mock Interview Engine API is running"}

def test_process_interview_turn_rest_no_input():
    # Should return an error if neither audio_file nor transcript is provided
    response = client.post("/api/interview/turn", data={"resume_context": "test"})
    assert response.status_code == 200
    assert "error" in response.json()
