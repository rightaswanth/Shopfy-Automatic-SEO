"""API Endpoints related to user authentication."""

from flask import request, jsonify, g, render_template
from flask_httpauth import HTTPBasicAuth, HTTPTokenAuth
from app.api import bp
from app.services import CRUD, BadRequest, Unauthorized, InternalError, Forbidden, send_email
from app.models import User, remove_user_token
from config import Config_is
from app.services import AuthService

auth = HTTPBasicAuth()
tokenAuth = HTTPTokenAuth(scheme='Token')
auth_service = AuthService()
crud = CRUD()


@auth.verify_password
def verify_password(email: str, password: str) -> bool:
    """Verify user email and password in login.

       If a region is not specified, the bucket is created in the S3 default
       region (us-east-1).

       :param email: email address string entered by user in login
       :param password: String password entered by user during login
       :return: True matched email and password
       """
    user = User.query.filter_by(email=email).first()
    if not user:
        raise BadRequest("Incorrect Email")
    if not user.is_active:
        raise Forbidden('Your account has been suspended')
    if not user.registered:
        raise Unauthorized("Please register first and try again")
    if user.check_password(password):
        g.user = user
        return True
    else:
        raise BadRequest('Wrong password')


@tokenAuth.verify_token
def verify_token(token: str) -> bool:
    user = User.verify_auth_token(token)
    if user:
        g.user = user
        return True
    raise Unauthorized()


@bp.route('/auth/login', methods=['POST'])
def login_user():
    """
    Login to the application with email address and password in
    """
    print(f"User login {request.json}")
    verify_password(request.json.get('email', ' ').lower().strip(), request.json.get('password', ' ').strip())
    token = g.user.generate_auth_token()
    return jsonify({'data': g.user.login_to_dict(), 'auth_token': token, 'status': 200}), 200


@bp.route('/auth/forgot_password', methods=['POST'])
def forgot_password_req():
    """
    Input email address to if forgot the password and reset password link will be sent in email
    """
    first_name, token = auth_service.forgot_password(request.json.get('email', '').strip().lower())
    password_reset_form = render_template("reset_template.html", first_name=first_name,
                                          reset_url=f"{Config_is.FRONT_END_PASSWORD_RESET_URL}/{token}")
    send_an_email = send_email(to_email=request.json.get('email').lower(), html_content=password_reset_form,
                               subject='Reset Password')
    if send_an_email:
        return jsonify({'message': 'Please check your inbox', 'status': 200}), 200
    raise InternalError()


@bp.route('/auth/reset_password', methods=['PATCH'])
def reset_password_req():
    print(f"Reset password: {request.json}")
    if not User.verify_auth_token(request.headers.get('Authorization', '').split(' ')[-1], 3600):
        raise Forbidden()
    if request.json.get('new_password') != request.json.pop('confirm_password', None):
        raise BadRequest('Enter the password correctly.')
    if auth_service.new_password(g.user['id'], request.json['new_password']):
        return jsonify({'message': 'Password has been changed successfully', 'status': 200}), 200
    return InternalError()


@bp.route('/auth/logout', methods=['GET'])
@tokenAuth.login_required()
def logout():
    remove_user_token(g.user['id'], request.headers.get('Authorization', '').replace('Token ', '').strip())
    return jsonify({'message': 'Success', 'status': 200}), 200


@bp.route('/test')
def test_api():
    return jsonify({'message': 'Success', 'status': 200}), 200
