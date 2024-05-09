#to create route blueprints
from flask import Blueprint, jsonify, request
#--

login_routes = Blueprint('login_routes', __name__)

#to access the Users table
from models import Users
from database import db
from sqlalchemy import inspect
#--

#to handle password hashing
from werkzeug.security import generate_password_hash, check_password_hash 
#--

#to create access and refresh tokens
from flask_jwt_extended import create_access_token, create_refresh_token
#--

#params : username, password, email
@login_routes.route('/create_user', methods=['POST'])
def create_user():
    try:
        data = request.get_json()
        username = data['username']
        email = data['email']
        hashed_password = generate_password_hash(data['password'])

        user = Users(username=username, email=email, hashed_password=hashed_password)
        db.session.add(user)
        db.session.commit()
        return {"message": "User created successfully"}, 200
    except Exception as e:
        return {"message": "The user cannot be created"}, 400

@login_routes.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email', None)
    password = data.get('password', None)

    user = Users.query.filter_by(email=email).first()
    if user and check_password_hash(user.hashed_password, password):
        user_id = user.id
        access_token = create_access_token(identity=user_id)
        refresh_token = create_refresh_token(identity=user_id)
        return jsonify(access_token=access_token, refresh_token=refresh_token), 200

    return jsonify({"msg": "Bad username or password"}), 401

from flask_jwt_extended import jwt_required, get_jwt_identity, create_access_token
@login_routes.route('/refresh', methods=['GET'])
@jwt_required(refresh=True)
def refresh():
    """
    Refreshes the access token for the current user.

    Returns:
        A JSON response containing the new access token.
    """
    current_user = get_jwt_identity()
    new_access_token = create_access_token(identity=current_user)
    return jsonify(access_token=new_access_token), 200