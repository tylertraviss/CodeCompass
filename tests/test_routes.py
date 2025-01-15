def test_dashboard_route(client):
    """Test the dashboard route."""
    response = client.get('/')
    assert response.status_code == 200
    assert b"Dashboard" in response.data


def test_about_us_route(client):
    """Test the about us page."""
    response = client.get('/about')
    assert response.status_code == 200
    assert b"About Us" in response.data


def test_question_route(client):
    """Test the question page with a valid question ID."""
    response = client.get('/question/1')
    assert response.status_code == 200
    assert b"Question" in response.data  # Adjust based on your template content


def test_question_route_invalid(client):
    """Test the question page with an invalid question ID."""
    response = client.get('/question/999')
    assert response.status_code == 404
    assert b"Question not found" in response.data
