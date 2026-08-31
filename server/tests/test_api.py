import pytest
from fastapi.testclient import TestClient
from core.gateway import app

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Mock Interview Engine API is running"
    assert data["engine"] == "NVIDIA STS (Speech-to-Speech)"

def test_process_interview_turn_rest_no_input():
    # Should return an error if neither audio_file nor transcript is provided
    response = client.post("/api/interview/turn", data={"resume_context": "test"})
    assert response.status_code == 200
    assert "error" in response.json()

def test_process_interview_turn_rest_with_transcript():
    response = client.post(
        "/api/interview/turn",
        data={
            "transcript": "I specialize in backend design with Python and microservices.",
            "resume_context": "Senior Software Engineer"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "user_transcript" in data
    assert "sts_model" in data
    assert "sts_audio_length" in data
