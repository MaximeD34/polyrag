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
@user_routes.route('/db_drop_all', methods=['GET'])
def db_drop_all():
    db.drop_all()
    db.create_all()

    import os

    #remove all the files
    storage_path = os.getenv('STORAGE_PATH', '../local_test_persistent_storage/')
    import shutil
    try:
        shutil.rmtree(storage_path)
    except:
        return 'Error while deleting the storage path'
        pass
    return 'Database dropped and recreated'


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

from models import EmbeddingStatus, StatusEnum

# class StatusEnum(Enum):
#     pending = 'pending'
#     done = 'done'
#     failed = 'failed'

# class EmbeddingStatus(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     file_id = db.Column(db.Integer, db.ForeignKey('files.id'), nullable=False)
#     status = db.Column(SQLEnum(StatusEnum), nullable=False) #the status of the embedding

#     def __repr__(self):
#         return '<Embedding %r>' % self.status
    

#returns all the private files status of the current user
@user_routes.route('/private_files_status', methods=['GET'])
@jwt_required()
def private_files_status():

    current_user_id = get_jwt_identity()
    embeddingStatus = db.session.query(EmbeddingStatus).join(Files, EmbeddingStatus.file_id == Files.id).filter(Files.user_id == current_user_id).all()
    
    embeddingStatus = [{"file_id": embedding.file_id, 
                        "status": embedding.status.value} for embedding in embeddingStatus]
    return jsonify(embeddingStatus), 200

#returns all the public files status
@user_routes.route('/public_files_status', methods=['GET'])
@jwt_required()
def public_files_status():

    current_user_id = get_jwt_identity()
    embeddingStatus = db.session.query(EmbeddingStatus).join(Files, EmbeddingStatus.file_id == Files.id).filter(and_(Files.is_public == True, Files.user_id != current_user_id)).all()
    
    embeddingStatus = [{"file_id": embedding.file_id, 
                        "status": embedding.status.value} for embedding in embeddingStatus]
    return jsonify(embeddingStatus), 200