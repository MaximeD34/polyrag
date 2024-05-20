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

from flask import make_response
from flask_jwt_extended import set_access_cookies, set_refresh_cookies

@login_routes.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email', None)
    password = data.get('password', None)

    print("login", email, password)

    user = Users.query.filter_by(email=email).first()
    if user and check_password_hash(user.hashed_password, password):
        user_id = user.id
        access_token = create_access_token(identity=user_id)
        refresh_token = create_refresh_token(identity=user_id)

        # Create a response and set the access and refresh tokens as HttpOnly cookies
        response = make_response(jsonify({"msg": "Login successful"}), 200)
        set_access_cookies(response, access_token)
        set_refresh_cookies(response, refresh_token)
        return response

    return jsonify({"msg": "Bad username or password"}), 401

from flask_jwt_extended import jwt_required, get_jwt_identity, create_access_token
@login_routes.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """
    Refreshes the access token for the current user.

    Returns:
        A response with a new access token in a HttpOnly cookie
    """
    current_user = get_jwt_identity()
    new_access_token = create_access_token(identity=current_user)

    # Create a response and set the new access token as a HttpOnly cookie
    response = make_response(jsonify({"msg": "Access token refreshed"}), 200)
    set_access_cookies(response, new_access_token)
    return response

#TODO put all the env in a file
import os

@login_routes.route('/logout', methods=['POST'])
def logout():
    response = make_response({"msg": "Logout successful"})
    if os.getenv('FLASK_ENV') == 'production':
        domain = ".cluster-ig3.igpolytech.fr"
    else:
        domain = "localhost"
    response.delete_cookie('access_token_cookie', domain=domain)
    response.delete_cookie('csrf_access_token', domain=domain)
    response.delete_cookie('refresh_token_cookie', domain=domain)
    response.delete_cookie('csrf_refresh_token', domain=domain)
    return response

