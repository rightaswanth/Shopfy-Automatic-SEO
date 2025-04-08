from flask import jsonify, request
from app.api import bp
from app import logging

@bp.route('/', methods=["GET"])
def index():
    print(request.json)
    print(request.args)
    logging.info(request.args)
    try:
        request.args['name']
    except Exception as e:
        logging.error(f"input  is {request.args} --> {str(e)}")
    return jsonify({"message": "Success", "status": 200}), 200


@bp.route('/incoming/', methods=["GET", "POST"])
def incoming():
    print(request.json)
    print(request.args)
    return jsonify({"message": "Success"}), 200


@bp.route('/outgoing/', methods=["GET", "POST"])
def outgoing():
    print(request.json)
    print(request.args)
    return jsonify({"message": "Success"}), 200
