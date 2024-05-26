#to create route blueprints
from flask import Blueprint, jsonify, request
#--

#for the database
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import and_, not_
from database import db
from models import Users, Files
#--

user_routes = Blueprint('user_routes', __name__)

@user_routes.route('/')
def hello():
    return 'Polyrag backend v 20/05 1806'

from database import db
from sqlalchemy import inspect

# ---------
# TODO TO REMOVE (debugging purposes)

#TODO remove this route
@user_routes.route('/db_selectAll/<table_name>', methods=['GET'])
def db_selectAll(table_name):
    inspector = inspect(db.engine)

    if table_name in inspector.get_table_names():
        table = db.Model.metadata.tables[table_name]
        query = db.session.query(table).all()
        return jsonify([row._asdict() for row in query])
    else:
        return {"error": "Table not found"}, 404

# TODO TO REMOVE (debugging purposes)
# ---------

#to remove all the db and the files
#TODO remove this route 
import logging
@user_routes.route('/db_drop_all', methods=['GET'])
def db_drop_all():
    try:
        db.drop_all()
        db.create_all()
    except Exception as e:
        logging.error("Error occurred while dropping and creating all tables: %s", e)
        return 'Error occurred while dropping and creating all tables', 500

    import os

    #remove all the files
    storage_path = os.getenv('STORAGE_PATH', '../local_test_persistent_storage/')
    import shutil
    try:
        shutil.rmtree(storage_path)
    except Exception as e:
        logging.error("Error occurred while deleting the storage path: %s", e)
        return 'Error while deleting the storage path', 500

    return 'Database dropped and recreated', 200

from models import Users, Admin

from flask_jwt_extended import jwt_required, get_jwt_identity

@user_routes.route('/user_infos', methods=['GET'])
@jwt_required()
def user_infos():

    current_user_id = get_jwt_identity()
    user = Users.query.filter_by(id=current_user_id).first()
    if user is None:
        return {"error": "User not found"}, 404
    else:
        is_admin = Admin.query.filter_by(id_user=current_user_id).first() is not None
        return jsonify(username=user.username, email=user.email, is_admin=is_admin), 200

#returns all the files of the current user
@user_routes.route('/user_files', methods=['GET'])
@jwt_required()
def user_files():
    current_user_id = get_jwt_identity()
    files = db.session.query(Files.id, Files.file_name, Files.is_public, Files.user_id).filter(Files.user_id == current_user_id).all()
    files = [{"id": file.id, 
              "file_name": file.file_name, 
              "is_public": file.is_public,
              "author": db.session.query(Users.username).filter(Users.id == file.user_id).first()[0]
              } for file in files]
    return jsonify(files), 200


#returns all the public files EXCEPT the ones of the current user
@user_routes.route('/all_public_files', methods=['GET'])
@jwt_required()
def all_public_files():
    current_user_id = get_jwt_identity()
    files = db.session.query(Files.id, Files.file_name, Files.is_public, Files.user_id).filter(and_(Files.is_public == True, Files.user_id != current_user_id)).all()

    files = [{"id": file.id, 
              "file_name": file.file_name, 
              "is_public": file.is_public, 
              "author": db.session.query(Users.username).filter(Users.id == file.user_id).first()[0]
              } for file in files]
    return jsonify(files), 200

from models import EmbeddingStatus

#returns all the private files status of the current user
@user_routes.route('/private_files_status', methods=['GET'])
@jwt_required()
def private_files_status():

    current_user_id = get_jwt_identity()
    embeddingStatus = db.session.query(EmbeddingStatus).join(Files, EmbeddingStatus.file_id == Files.id).filter(Files.user_id == current_user_id).all()
    
    embeddingStatus = [{"file_id": embedding.file_id, 
                        "status": embedding.status} for embedding in embeddingStatus]
    return jsonify(embeddingStatus), 200

#returns all the public files status
@user_routes.route('/public_files_status', methods=['GET'])
@jwt_required()
def public_files_status():

    current_user_id = get_jwt_identity()
    embeddingStatus = db.session.query(EmbeddingStatus).join(Files, EmbeddingStatus.file_id == Files.id).filter(and_(Files.is_public == True, Files.user_id != current_user_id)).all()
    
    embeddingStatus = [{"file_id": embedding.file_id, 
                        "status": embedding.status} for embedding in embeddingStatus]
    return jsonify(embeddingStatus), 200

from models import Query

#returns the history of the current user
@user_routes.route('/history', methods=['GET'])
@jwt_required()
def history():
    current_user_id = get_jwt_identity()

    queries = db.session.query(Query, Users.username).join(Users, Users.id == Query.user_id).filter(Query.user_id == current_user_id).all()

    # For each query, get the file names from the Files table
    for query, username in queries:
        file_names = db.session.query(Files.file_name).filter(Files.id.in_(query.used_files)).all()
        query.file_names = [file[0] for file in file_names]

    queries = [{"id": query.id,
            "user_id": query.user_id,
            "used_files": query.used_files,
            "question": query.question,
            "instructions": query.instructions,
            "answer": query.answer,
            "query_date": query.query_date,
            "username": username,
            "file_names": query.file_names
            
            } for query, username in queries]
    
    return jsonify(queries), 200

    
#returns the history of all the users (only for admins)
@user_routes.route('/all_history', methods=['GET'])
@jwt_required()
def all_history():
    current_user_id = get_jwt_identity()
    if Admin.query.filter_by(id_user=current_user_id).first() is None:
        return {"error": "Unauthorized access"}, 401

    queries = db.session.query(Query, Users.username).join(Users, Users.id == Query.user_id).all()

    # For each query, get the file names from the Files table
    for query, username in queries:
        file_names = db.session.query(Files.file_name).filter(Files.id.in_(query.used_files)).all()
        query.file_names = [file[0] for file in file_names]

    queries = [{"id": query.id,
            "user_id": query.user_id,
            "used_files": query.used_files,
            "question": query.question,
            "instructions": query.instructions,
            "answer": query.answer,
            "query_date": query.query_date,
            "username": username,
            "file_names": query.file_names
            
            } for query, username in queries]

    return jsonify(queries), 200

#returns the analytics of the current user
@user_routes.route('/analytics', methods=['GET'])
@jwt_required()
def analytics():
    current_user_id = get_jwt_identity()

    nb_queries = db.session.query(Query).filter(Query.user_id == current_user_id).count() 
    username = db.session.query(Users.username).filter(Users.id == current_user_id).first()[0]
    if username is None:
        return {"error": "User not found"}, 404

    return jsonify([{"id": current_user_id,
                    "username": username,
                     "nb_queries": nb_queries}]), 200

#returns the analytics of all the users (only for admins)
@user_routes.route('/all_analytics', methods=['GET'])
@jwt_required()
def all_analytics():
    current_user_id = get_jwt_identity()
    if Admin.query.filter_by(id_user=current_user_id).first() is None:
        return {"error": "Unauthorized access"}, 401

    analytics = db.session.query(Query.user_id, Users.username, db.func.count(Query.id)).join(Users, Users.id == Query.user_id).group_by(Query.user_id, Users.username).all()
    
    analytics = [{"id": user_id,
                  "username": username,
                  "nb_queries": nb_queries} for user_id, username, nb_queries in analytics]

    return jsonify(analytics), 200