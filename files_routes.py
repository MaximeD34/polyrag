#to create route blueprints
from flask import Blueprint, jsonify, request
#--

files_routes = Blueprint('files_routes', __name__)

#to access the Users table
from models import Users, Files
from database import db
from sqlalchemy import inspect
#--

#to access the os directories
import os
#--

#to generate secure filenames for the files
from werkzeug.utils import secure_filename
#--

#to generate the embeddings
from embeddings_manager import force_create_embedding
#--

def check_document_name(file_name):
    
    if file_name == '':
        return {"error": "No file name"}, 400
    
    #check if there is an extension
    if '.' not in file_name:
        return {"error": "No file extension"}, 400

    #check if the extension is supported
    allowed_extensions = ['txt', 'pdf']
    file_extension = file_name.split('.')[-1]
    if file_extension not in allowed_extensions:
        return {"error": "Invalid file extension"}, 400
    
    return None

from flask_jwt_extended import jwt_required, get_jwt_identity
@files_routes.route('/upload', methods=['POST'])
@jwt_required()
def upload_file():

    if 'file' not in request.files:
        return {"error": "No file selected"}, 400

    if 'is_public' not in request.form:
        return {"error": "No is_public part"}, 400
    
    file = request.files['file']
    is_public = request.form['is_public']

    #get a secure filename
    secured_filename = secure_filename(file.filename)

    #check if the file name is valid
    check = check_document_name(secured_filename)
    if check is not None:
        return check #return the error message
    
    #check if the document is not empty
    if file.read() == b'':
        return {"error": "Empty file"}, 400
    file.seek(0) #reset the file pointer
    
    if is_public == 'true':
        is_public = True
    elif is_public == 'false':
        is_public = False
    else:
        return {"error": "Invalid is_public value"}, 400

    #get the file extension (we already checked it exists and is valid)
    file_extension = secured_filename.split('.')[-1]

    #create the file object in the database
    current_user_id = get_jwt_identity()
    file_entity = Files(user_id=current_user_id, 
                 file_name=secured_filename, 
                 file_extension=file_extension, 
                 is_public=is_public)
    
    db.session.add(file_entity)
    db.session.commit()

    storage_path = os.getenv('STORAGE_PATH', '../local_test_persistent_storage/')

    storing_path = os.path.join(storage_path, str(current_user_id)) #the path where the file will be stored
    
    #ensures the user directory exists or creates it
    os.makedirs(storing_path, exist_ok=True)

    #saves the file in the user folder with its id in the file name
    file.save(os.path.join(storing_path, str(file_entity.id) + "_" + secured_filename))

    #creates the embedding for the file
    force_create_embedding(storage_path, file_entity.id, current_user_id, secured_filename)

    return {"message": "File uploaded successfully"}, 200

@files_routes.route('/modify/<int:file_id>', methods=['PATCH'])
@jwt_required()
def modify_file(file_id):

    if 'is_public' not in request.form:
        return {"error": "No is_public part"}, 400
    if 'file_name' not in request.form:
        return {"error": "No file_name part"}, 400

    current_user_id = get_jwt_identity()

    file = Files.query.filter_by(id=file_id).first()
    if file is None:
        return {"error": "File not found"}, 404

    if file.user_id != current_user_id:
        return {"error": "Unauthorized"}, 401

    is_public = request.form['is_public']

    #get a secure filename
    secured_filename = secure_filename(request.form['file_name'])
    print(secured_filename)

    #check if the file name is valid
    check = check_document_name(secured_filename)
    if check is not None:
        return check
    
    #check if the extension is the same
    if file.file_extension != secured_filename.split('.')[-1]:
        return {"error": "The extension of the file cannot be changed"}, 400
    
    if is_public == 'true':
        is_public = True
    elif is_public == 'false':
        is_public = False
    else:
        return {"error": "Invalid is_public value"}, 400
    
    #rename the file in the storage
    storage_path = os.getenv('STORAGE_PATH', '../local_test_persistent_storage/')
    storing_path = os.path.join(storage_path, str(current_user_id))
    os.rename(os.path.join(storing_path, str(file.id) + "_" + file.file_name), os.path.join(storing_path, str(file.id) + "_" + secured_filename))

    #update the file in the database
    file.file_name = secured_filename
    file.is_public = is_public
    file.file_extension = secured_filename.split('.')[-1]

    db.session.commit()

    return {"message": "File modified successfully"}, 200

@files_routes.route('/delete/<int:file_id>', methods=['DELETE'])
@jwt_required()
def delete_file(file_id):

    current_user_id = get_jwt_identity()

    file = Files.query.filter_by(id=file_id).first()
    if file is None:
        return {"error": "File not found"}, 404

    if file.user_id != current_user_id:
        return {"error": "Unauthorized"}, 401

    #delete the file from the storage
    storage_path = os.getenv('STORAGE_PATH', '../local_test_persistent_storage/')
    storing_path = os.path.join(storage_path, str(current_user_id))
    os.remove(os.path.join(storing_path, str(file.id) + "_" + file.file_name))

    #delete the file from the database
    db.session.delete(file)
    db.session.commit()

    return {"message": "File deleted successfully"}, 200

#for debugging purposes
#TODO remove this route
@files_routes.route('/list_files')
def list_files():
    try:
        storage_path = os.getenv('STORAGE_PATH', '../test_storage') #TODO import from app.py instead of redefining it
        files = os.listdir(storage_path)
        return '<br>'.join(files)
    except Exception as e:
        return str(e)

#for debugging purposes
#TODO remove this route
@files_routes.route('/debug', methods=['GET'])
def debug():
    try:
        directories = os.listdir('/app')
    except Exception as e:
        directories = str(e)
    return {"directories": directories}, 200