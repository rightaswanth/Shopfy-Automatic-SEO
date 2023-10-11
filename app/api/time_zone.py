from flask import request, g, jsonify

from app.api import bp
from app.models import TimeZone
from app.services.crud import CRUD
from app.services.auth import admin_authorizer
from app.api.user import tokenAuth


@bp.route('/time_zone', methods=["PUT"])
@tokenAuth.login_required
@admin_authorizer
def edit_time_zone():
    CRUD.update(TimeZone, {"id": 1}, request.json)
    return jsonify({"message": "Successfully updated the time zone", "status": 200}), 200


@bp.route('/time_zone', methods=["GET"])
@tokenAuth.login_required
def get_time_zone():
    time_zone = TimeZone.query.filter_by(id=1).first()
    return jsonify(
        {"data": {"zone": time_zone.zone, "value": time_zone.value}, "message": "Success", "status": 200}), 200

