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
    
from sqlalchemy import DDL
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.dialects.postgresql import ENUM

class CreateEnumType(DDL):
    """Create an ENUM type."""

    def __init__(self, enum):
        self.enum = enum
        DDL.__init__(self, "CREATE TYPE %s AS ENUM (%s)" % (enum.name, enum.enum_class))

    def execute(self, bind, schema, **kw):
        try:
            DDL.execute(self, bind, schema, **kw)
        except ProgrammingError as e:
            if 'already exists' not in str(e.orig):
                raise e

class StatusEnum(ENUM):
    """Enum type for status."""

    def create(self, bind=None, checkfirst=False):
        if not checkfirst or not bind.dialect.has_type(bind, self.name):
            bind.execute(CreateEnumType(self))

status_enum = StatusEnum('pending', 'done', 'failed', name='statusenum')

class EmbeddingStatus(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    file_id = db.Column(db.Integer, db.ForeignKey('files.id'), nullable=False)
    status = db.Column(status_enum, nullable=False) #the status of the embedding

    def __repr__(self):
        return '<Embedding %r>' % self.status
    
