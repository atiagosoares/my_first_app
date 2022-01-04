#flask 
from flask import Flask, render_template, session, redirect
from flask.helpers import url_for
from markupsafe import escape

#socketio
from flask_socketio import SocketIO, join_room, leave_room

#sql
from flask_sqlalchemy import SQLAlchemy
import sqlite3
from sqlalchemy.orm import relationship

#general utilities
from datetime import datetime
import random

#from logging import PlaceHolder
import json
from werkzeug.datastructures import CharsetAccept

app = Flask(__name__)
app.config.from_object('config')
db = SQLAlchemy(app)
socket = SocketIO(app)

from whoami.controllers import con
app.register_blueprint(con)

db.create_all()