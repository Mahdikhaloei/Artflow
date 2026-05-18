import io
from unittest.mock import patch

from core.tests.factories import PosterRequestFactory


def test_get_poster_request_list(client, db_session):
    """
    Verifies that the GET /poster-request/ endpoint returns a list of poster requests.
    """
    PosterRequestFactory._meta.sqlalchemy_session = db_session

    PosterRequestFactory.create_batch(2)

    response = client.get("/api/v1/poster-request/")
    assert response.status_code == 200

    data = response.get_json()
    assert "results" in data
    assert isinstance(data["results"], list)
    assert len(data["results"]) == 2


def test_post_poster_request(client, db_session):
    """
    Verifies that the POST /poster-request/ endpoint creates a new poster request
    and triggers the Celery task chain.
    """
    dummy_image = (io.BytesIO(b"test image data"), "test.png")

    with patch("core.api.resources.poster.chain") as mock_chain:
        mock_chain.return_value.apply_async.return_value.id = "fake-task-id"

        response = client.post(
            "/api/v1/poster-request/",
            data={
                "text_subtitle": "Test Subtitle",
                "reward_amount": "5000",
                "email": "test@example.com",
                "image": dummy_image
            },
            content_type="multipart/form-data"
        )

        assert response.status_code == 201
        data = response.get_json()
        assert "result" in data
        assert "registered" in data["result"]

        mock_chain.assert_called_once()
        mock_chain.return_value.apply_async.assert_called_once()
