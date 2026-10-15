
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.db.session import get_db
from app.core.config import settings
from app.services.llm import (
    LLMConfigurationError,
    LLMProviderError,
)

client = TestClient(app)


@pytest.fixture
def mock_db():
    """Override the database dependency so tests never access PostgreSQL."""
    db = object()
    app.dependency_overrides[get_db] = lambda: db

    yield db

    app.dependency_overrides.clear()


@pytest.fixture
def sample_result():
    """Create a chunk and document resembling the real ORM objects."""
    document = SimpleNamespace(
        id=1,
        filename="employee_handbook.pdf",
    )

    chunk = SimpleNamespace(
        id=10,
        document_id=1,
        chunk_index=0,
        content="Employees receive 20 days of annual leave.",
        page_number=3,
        document=document,
    )

    return chunk, 0.87


def test_chat_success(mock_db, sample_result):
    with (
        patch("app.api.chat.settings.groq_api_key", "test-key"),
        patch(
            "app.api.chat.search_chunks",
            return_value=[sample_result],
        ) as mock_search,
        patch(
            "app.api.chat.generate_answer",
            return_value="Employees receive 20 days of annual leave. [S1]",
        ) as mock_generate,
    ):
        response = client.post(
            "/chat/",
            json={
                "question": "How many days of annual leave do employees receive?",
                "limit": 5,
            },
        )

    assert response.status_code == 200

    data = response.json()
    assert data["question"] == (
        "How many days of annual leave do employees receive?"
    )
    assert "20 days" in data["answer"]
    assert len(data["sources"]) == 1

    source = data["sources"][0]
    assert source["source_id"] == "S1"
    assert source["document_id"] == 1
    assert source["filename"] == "employee_handbook.pdf"
    assert source["page_number"] == 3
    assert source["chunk_index"] == 0
    assert source["similarity_score"] == 0.87
    assert "20 days" in source["content"]

    mock_search.assert_called_once()
    mock_generate.assert_called_once()


def test_chat_returns_message_when_no_relevant_chunks(mock_db):
    with (
        patch("app.api.chat.settings.groq_api_key", "test-key"),
        patch("app.api.chat.search_chunks", return_value=[]) as mock_search,
        patch("app.api.chat.generate_answer") as mock_generate,
    ):
        response = client.post(
            "/chat/",
            json={"question": "What is the company's office address?"},
        )

    assert response.status_code == 200

    data = response.json()
    assert "couldn't find" in data["answer"].lower()
    assert data["sources"] == []

    mock_search.assert_called_once()
    mock_generate.assert_not_called()


def test_chat_rejects_blank_question(mock_db):
    with patch("app.api.chat.settings.groq_api_key", "test-key"):
        response = client.post(
            "/chat/",
            json={"question": "   "},
        )

    assert response.status_code == 422


def test_chat_rejects_missing_question(mock_db):
    with patch("app.api.chat.settings.groq_api_key", "test-key"):
        response = client.post("/chat/", json={})

    assert response.status_code == 422


def test_chat_rejects_question_over_maximum_length(mock_db):
    with patch("app.api.chat.settings.groq_api_key", "test-key"):
        response = client.post(
            "/chat/",
            json={"question": "a" * 2001},
        )

    assert response.status_code == 422


def test_chat_rejects_invalid_limit(mock_db):
    with patch("app.api.chat.settings.groq_api_key", "test-key"):
        response = client.post(
            "/chat/",
            json={"question": "What is in the document?", "limit": 0},
        )

    assert response.status_code == 422


def test_chat_returns_503_when_llm_not_configured(mock_db):
    with patch("app.api.chat.settings.groq_api_key", ""):
        response = client.post(
            "/chat/",
            json={"question": "Summarize the document."},
        )

    assert response.status_code == 503
    assert response.json()["detail"] == (
        "The language model is not configured."
    )


def test_chat_returns_404_for_missing_document(mock_db):
    with (
        patch("app.api.chat.settings.groq_api_key", "test-key"),
        patch("app.api.chat.get_document_with_chunks", return_value=None),
        patch("app.api.chat.search_chunks") as mock_search,
    ):
        response = client.post(
            "/chat/",
            json={
                "question": "Summarize this document.",
                "document_id": 99999,
            },
        )

    assert response.status_code == 404
    assert response.json()["detail"] == "Document not found."
    mock_search.assert_not_called()


def test_chat_returns_503_for_llm_configuration_error(
    mock_db,
    sample_result,
):
    with (
        patch("app.api.chat.settings.groq_api_key", "test-key"),
        patch(
            "app.api.chat.search_chunks",
            return_value=[sample_result],
        ),
        patch(
            "app.api.chat.generate_answer",
            side_effect=LLMConfigurationError("Missing model configuration"),
        ),
    ):
        response = client.post(
            "/chat/",
            json={"question": "Summarize the document."},
        )

    assert response.status_code == 503
    assert response.json()["detail"] == "The language model is not configured correctly."


def test_chat_returns_502_for_llm_provider_error(mock_db, sample_result):
    with (
        patch("app.api.chat.settings.groq_api_key", "test-key"),
        patch(
            "app.api.chat.search_chunks",
            return_value=[sample_result],
        ),
        patch(
            "app.api.chat.generate_answer",
            side_effect=LLMProviderError("Provider unavailable"),
        ),
    ):
        response = client.post(
            "/chat/",
            json={"question": "Summarize the document."},
        )

    assert response.status_code == 502
    assert response.json()["detail"] == "The language model request failed."



def test_chat_does_not_expose_unexpected_exception(mock_db, sample_result):
    with (
        patch("app.api.chat.settings.groq_api_key", "test-key"),
        patch(
            "app.api.chat.search_chunks",
            return_value=[sample_result],
        ),
        patch(
            "app.api.chat.generate_answer",
            side_effect=RuntimeError("internal-secret-detail"),
        ),
    ):
        response = client.post(
            "/chat/",
            json={"question": "Summarize the document."},
        )

    assert response.status_code == 502
    assert response.json()["detail"] == (
        "The language model request failed."
    )
    assert "internal-secret-detail" not in response.text
