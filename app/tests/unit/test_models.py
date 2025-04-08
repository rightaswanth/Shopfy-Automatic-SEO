from app.models import User


def test_new_user_with_fixture(new_user):
    """
    Given a user model
    When a new user is created
    Then check the email, hashed_password, and role fields are defined correctly
    """
    assert new_user.email == "arun_n_a@abacies.com"
    assert new_user.first_name == "FlaskIsAwesome"
