from functools import wraps
from flask import g

from .crud import CRUD
from .custom_errors import NoContent, Forbidden, Conflict
from app.models import User, remove_user_token
from .user import upload_user_profile_pic

crud = CRUD()


class AuthService(object):

    def forgot_password(self, email: str) -> tuple:
        user = User.query.filter_by(email=email, is_active=True).first()
        if not user:
            raise NoContent("Please enter a valid email address.")
        if not user.registered:
            raise Forbidden("Please register first")
        token = user.generate_auth_token()
        return user.first_name, token

    def new_invitee(self, data: dict, file_is: object = None) -> bool:
        """
        User registration from email invitation
        """
        user_obj = User.query.filter_by(id=g.user['id']).first()
        if user_obj.registered:
            raise Conflict('User already registered')
        user_obj.hash_password(data.pop('password'))
        if data.get('role_id'):
            data.pop('role_id')
        if file_is:
            avatar = upload_user_profile_pic(file_is['file'], user_obj)
            if avatar:
                data |= avatar
        print(data)
        crud.update(User, {'id': user_obj.id}, {'registered': True, 'is_active': True, **data})
        remove_user_token(g.user['id'])
        return True

    def new_password(self, user_id: int, password: str) -> bool:
        user = User.query.get(user_id)
        user.hash_password(password)
        crud.db_commit()
        remove_user_token(user_id)
        return True


def admin_authorizer(func):
    @wraps(func)
    def inner(*args, **kwargs):
        if g.user['role_id'] == 2:
            return func(*args, **kwargs)
        raise Forbidden()

    return inner
