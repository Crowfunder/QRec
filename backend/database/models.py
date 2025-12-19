import datetime
import sqlalchemy as sa
from sqlalchemy.orm import mapped_column, relationship
from flask_sqlalchemy import SQLAlchemy

# Here you can read about useful column types (Integer, String, DateTime, etc...):
# https://docs.sqlalchemy.org/en/20/core/type_basics.html#generic-camelcase-types

# Here you can read about relationships between models:
# https://docs.sqlalchemy.org/en/20/orm/basic_relationships.html
# https://stackoverflow.com/questions/3113885/difference-between-one-to-many-many-to-one-and-many-to-many

# Here you can read about using models defined below to work
# with the database (creating rows, selecting rows, deleting rows, etc...):
# https://flask-sqlalchemy.palletsprojects.com/en/3.1.x/queries/



db = SQLAlchemy()
from dataclasses import dataclass


@dataclass
class Worker(db.Model):
    __tablename__ = 'workers'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    face_image = db.Column(db.Blob, nullable=False)
    expiration_date = db.Column(db.DateTime, nullable=False)
    secret = db.Column(db.String, nullable=False)
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "face_image": self.face_image,
            "expiration_date": self.expiration_date.isoformat() if self.expiration_date else None,
            "secret": self.secret
        }


@dataclass
class Entry(db.Model):
    __tablename__ = 'entries'
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now(datetime.UTC))
    worker_id = db.Column(db.Integer, db.ForeignKey('workers.id', ondelete='CASCADE'), nullable=True)
    code = db.Column(db.Integer, nullable=False)
    message = db.Column(db.String, nullable=False)
    face_image = db.Column(db.String, nullable=True)
    def to_dict(self):
        return {
            "id": self.id,
            "date": self.date.isoformat() if self.date else None,
            "worker_id": self.worker_id,
            "code": self.code,
            "message": self.message,
            "face_image": self.face_image
        }


