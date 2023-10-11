"""API Endpoints related to User."""

from flask import request, jsonify, g

from app.api import bp
from app.services.auth import AuthService, admin_authorizer
from .auth import tokenAuth
from app.services.custom_errors import BadRequest, NoContent, Forbidden
from app.models import User
from app.services import adding_new_user, edit_user_details, make_user_active_inactive, sent_email_invitation, \
    delete_organization_user, user_avatar_uploading, user_avatar_deleting
from config import Config_is

auth_service = AuthService()


@bp.route('/user', methods=['POST'])
@tokenAuth.login_required
@admin_authorizer
def add_new_users():
    """
    Add new user to an organization by sending an email invitation
    """
    adding_new_user(request.json)
    return jsonify({'message': 'Success', 'status': 200}), 200


@bp.route('/user/register_from_invitation', methods=['PUT'])
def user_registration_invitee():
    print(request.json)
    print(request.files)
    if not User.verify_auth_token(request.headers.get('Authorization', '').split(' ')[-1], 21600):
        raise Forbidden('Link is expired')
    if request.json.get('password') != request.json.pop('confirm_password', None):
        raise BadRequest('Password Mismatch.')
    auth_service.new_invitee(request.json, request.files)
    return jsonify({'message': 'Success', 'status': 200}), 200


@bp.route('/user/edit_my_avatar', methods=["PUT", "DELETE"])
@tokenAuth.login_required
def update_avatar():
    if request.method == "DELETE":
        user_avatar_deleting()
        return jsonify({'message': 'Success', 'status': 200}), 200
    avatar = user_avatar_uploading(request.files)
    return jsonify({'data': f"https://{Config_is.S3_BUCKET_NAME}.s3.us-east-1.amazonaws.com/{g.user['organization_id']}/avatar/{avatar}",'message': 'Success', 'status': 200}), 200


@bp.route('/user/edit_my_info', methods=["PUT"])
@tokenAuth.login_required
def edit_my_info():
    edit_user_details(g.user['id'], request.json)
    return jsonify({'message': 'Success', 'status': 200}), 200


@bp.route('/user/edit_other_user_info/<int:user_id>', methods=["PUT"])
@tokenAuth.login_required
@admin_authorizer
def edit_other_user_info(user_id):
    print(request.json)
    edit_user_details(user_id, request.json)
    return jsonify({'message': 'Success', 'status': 200}), 200


@bp.route('/user/make_user_active_inactive/<int:user_id>', methods=['PATCH'])
@tokenAuth.login_required
@admin_authorizer
def active_inactivate_user(user_id):
    print(request.json)
    print(user_id)
    make_user_active_inactive(user_id, request.json['is_active'])
    return jsonify({"message": "success", "status": 200}), 200


@bp.route('/user/paginated_list', methods=["GET"])
@tokenAuth.login_required
@admin_authorizer
def list_paginated_users():
    print(g.user)
    users = User.query.filter_by(organization_id=g.user['organization_id'], is_deleted=False).paginate(
        int(request.args.get('page', 1)), int(request.args.get('per_page', 10)), error_out=False)
    data = [u.to_dict(request.args['time_zone']) for u in users.items]
    if data:
        return jsonify({'data': data,
                        'pagination': {'total': users.total, 'current_page': users.page, 'per_page': users.per_page,
                                       'length': len(data)}, 'message': 'Success', 'status': 200}), 200
    raise NoContent()


@bp.route('/user/resend_invitation_email/<int:user_id>', methods=['POST'])
@tokenAuth.login_required
@admin_authorizer
def resend_invitation_email(user_id):
    u = User.query.filter_by(id=user_id, organization_id=g.user['organization_id'], registered=False,
                             is_active=True).first()
    if not u:
        raise BadRequest('Already registered or does not exist')
    token = u.generate_auth_token()  # token expires after 12 hours
    sent_email_invitation(u.first_name, u.last_name, u.email, token)
    return jsonify({'message': 'Success', 'status': 200}), 200


@bp.route('/user/<int:user_id>', methods=['DELETE'])
@tokenAuth.login_required
@admin_authorizer
def delete_user(user_id):
    delete_organization_user(user_id)
    return jsonify({'message': 'Success', 'status': 200}), 200
