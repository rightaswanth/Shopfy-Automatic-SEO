"""API Endpoints related to user authentication."""

from flask import request, jsonify, g, render_template
from flask_httpauth import HTTPBasicAuth, HTTPTokenAuth

from app.api import bp
from app.services.custom_errors import (BadRequest, Unauthorized, InternalError, Forbidden)
from app.services.sendgrid_email import send_email
from app.services.auth import AuthService
from app.models import User, remove_user_token
from config import Config_is

auth = HTTPBasicAuth()
tokenAuth = HTTPTokenAuth(scheme='Token')
auth_service = AuthService()


@auth.verify_password
def verify_password(email: str, password: str) -> bool:
    """Verify user email and password in login
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
    if not token:
        token = str(request.headers.get('Authorization', ''))
    token = token.split('Token ')[-1]
    if token:
        user_is = User.verify_auth_token(token)
        if user_is:
            g.user = user_is
            return True
    raise Unauthorized()


@bp.route('/auth/login', methods=['POST'])
def login_user():
    """
    Login to the application with email address and password in
    """
    verify_password(request.json.get('email', ' ').lower().strip(), request.json.get('password', ' ').strip())
    token = g.user.generate_auth_token()
    return jsonify({'data': g.user.login_to_dict(), 'auth_token': token, 'status': 200}), 200


@bp.route('/auth/forgot_password', methods=['POST'])
def forgot_password_req():
    """
        Input email address to if forgot the password and reset password link will be sent in email
        """
    name, token = auth_service.forgot_password(request.json.get('email', '').strip().lower())
    password_reset_form = render_template("reset_template.html", name=name,
                                          reset_url=f"{Config_is.FRONT_END_PASSWORD_RESET_URL}/{token}",
                                          unsubscribe_url=Config_is.UNSUBSCRIBE_LINK)
    send_an_email = send_email(to_email=request.json.get('email').lower(), html_content=password_reset_form,
                               subject='Aria Leads Reset Password')
    if send_an_email:
        return jsonify({'message': 'Please check your inbox', 'status': 200}), 200
    raise InternalError()


@bp.route('/auth/reset_password', methods=['PATCH'])
def reset_password_req():
    if len(request.json.get('new_password', '')) < 5:
        raise BadRequest('Password length is short. Please try another password')
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
