#to create route blueprints
from flask import Blueprint, jsonify, request
#--

user_routes = Blueprint('user_routes', __name__)

@user_routes.route('/')
def hello():
    return 'Hello World!'


from database import db
from sqlalchemy import inspect
@user_routes.route('/db_selectAll/<table_name>', methods=['GET'])
def db_selectAll(table_name):
    inspector = inspect(db.engine)

    if table_name in inspector.get_table_names():
        table = db.Model.metadata.tables[table_name]
        query = db.session.query(table).all()
        return jsonify([row._asdict() for row in query])
    else:
        return {"error": "Table not found"}, 404


from models import Users

from flask_jwt_extended import jwt_required, get_jwt_identity

@user_routes.route('/user_infos', methods=['GET'])
@jwt_required()
def user_infos():

    current_user_id = get_jwt_identity()
    user = Users.query.filter_by(id=current_user_id).first()
    if user is None:
        return {"error": "User not found"}, 404
    else:
        return jsonify(username=user.username, email=user.email), 200
