from flask import request, g, jsonify
from app.api import bp
from app.models import TimeZone
from app.services.crud import CRUD
from app.services.auth import is_super_admin
from app.api.user import tokenAuth

crud = CRUD()


@bp.route('/time_zone', methods=["PUT"])
@tokenAuth.login_required
@is_super_admin
def edit_time_zone():
    crud.update(TimeZone, {"id": 1}, request.json)
    return jsonify({"message": "Successfully updated the time zone", "status": 200}), 200


@bp.route('/time_zone', methods=["GET"])
@tokenAuth.login_required
def get_time_zone():
    time_zone = TimeZone.query.filter_by(id=1).first()
    return jsonify(
        {"data": {"zone": time_zone.zone, "value": time_zone.value}, "message": "Success", "status": 200}), 200

