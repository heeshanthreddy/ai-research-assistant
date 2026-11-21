from app.extensions import db
from datetime import datetime

class User(db.Model):  # This Python class represents a database table
    __tablename__ = "users"                          
    id = db.Column(db.Integer, primary_key=True)   # creating a column with integer datatype
    username = db.Column( db.String(100), nullable=False, unique=True ) # nullable = False make sures every user has username
    email = db.Column( db.String(120), nullable=False, unique=True )
    password_hash = db.Column( db.String(255), nullable=False )
    created_at = db.Column( db.DateTime, default=datetime.utcnow, nullable=False ) # utc -> a standard way of putting time in DB 
    projects = db.relationship( "Project", back_populates="user",cascade="all, delete-orphan")