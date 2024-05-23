from database import db

class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hashed_password = db.Column(db.String(255), nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)

    def __repr__(self):
        return '<Users %r>' % self.username
    
class Files(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False) #tells us the file path too
    file_name = db.Column(db.String(255), nullable=False) #without the path(e.g. file_name.txt)
    file_extension = db.Column(db.String(10), nullable=False) #the extension of the file (e.g. .txt, .jpg, .png)
    is_public = db.Column(db.Boolean, nullable=False) #if the file is public or not

    def __repr__(self):
        return '<File %r>' % self.file_name

class EmbeddingStatus(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    file_id = db.Column(db.Integer, db.ForeignKey('files.id'), nullable=False)
    status = db.Column(db.String(50), nullable=False) #the status of the embedding

    def __repr__(self):
        return '<Embedding %r>' % self.status
    