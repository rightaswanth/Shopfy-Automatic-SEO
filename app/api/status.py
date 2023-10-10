from flask import jsonify, request

from app.api import bp
from app import logging

@bp.route('/payload', methods=["POST"])
def index():
    print(request.json)
    print(request.form)
    print(request.args)
    return jsonify({"message": "Success", "status": 200})
