from app import create_app


def test_home_page_with_fixture(test_client):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/' page is requested (GET)
    THEN check that the response is valid
    """
    response = test_client.get('/v1/')
    import json
    assert response.status_code == 200
    response = json.loads(response.data)
    assert "Success" in response['message']
    assert response['status'] == 200
