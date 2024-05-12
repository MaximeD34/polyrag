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

from flask_jwt_extended import jwt_required, get_jwt_identity

@files_routes.route('/upload', methods=['POST'])
@jwt_required()
def upload_file():

    storage_path = os.getenv('STORAGE_PATH', '../local_test_persistent_storage/')

    if 'file' not in request.files:
        return {"error": "No file part"}, 400

    if 'is_public' not in request.form:
        return {"error": "No is_public part"}, 400

    file = request.files['file']
    if file.filename == '':
        return {"error": "No selected file"}, 400
    
    #check if there is an extension
    if '.' not in file.filename:
        return {"error": "No file extension"}, 400

    #check if the extension is supported
    allowed_extensions = ['txt', 'pdf']
    file_extension = file.filename.split('.')[-1]
    if file_extension not in allowed_extensions:
        return {"error": "Invalid file extension"}, 400
    
    #check if the document is not empty
    if file.read() == b'':
        return {"error": "Empty file"}, 400
    file.seek(0)

    is_public = request.form['is_public']
    if is_public == 'true':
        is_public = True
    elif is_public == 'false':
        is_public = False
    else:
        return {"error": "Invalid is_public value"}, 400

    #the filename the user will see, not the actual name of the stored file
    user_filename = secure_filename(file.filename)

    #create the file object in the database
    current_user_id = get_jwt_identity()
    file_entity = Files(user_id=current_user_id, 
                 file_name=user_filename, 
                 file_extension=file_extension, 
                 is_public=is_public)
    
    db.session.add(file_entity)
    db.session.commit()

    storing_path = os.path.join(storage_path, str(current_user_id)) #the path where the file will be stored
    
    #ensures the user directory exists or creates it
    os.makedirs(storing_path, exist_ok=True)

    #saves the file in the user folder with its id as file name
    file.save(os.path.join(storing_path, str(file_entity.id) + "_" + user_filename))

    return {"message": "File uploaded successfully"}, 200

@files_routes.route('/list_files')
def list_files():
    try:
        storage_path = os.getenv('STORAGE_PATH', '../test_storage')
        files = os.listdir(storage_path)
        return '<br>'.join(files)
    except Exception as e:
        return str(e)

@files_routes.route('/debug', methods=['GET'])
def debug():
    try:
        directories = os.listdir('/app')
    except Exception as e:
        directories = str(e)
    return {"directories": directories}, 200