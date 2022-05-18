import pytest
import app
from app import create_app
from app.models import User

"""
fixtures can be run with different scopes:

function - run once per test function (default scope)
class - run once per test class
module - run once per module (e.g., a test file)
session - run once per session
"""


@pytest.fixture(scope='module')
def new_user():
    user = User(email='arun_n_a@abacies.com', first_name='FlaskIsAwesome')
    return user


@pytest.fixture(scope='module')
def test_client():
    flask_app = create_app()

    # Create a test client using the Flask application configured for testing
    with flask_app.test_client() as testing_client:
        # Establish an application context
        with flask_app.app_context():
            yield testing_client  # this is where the testing happens!
