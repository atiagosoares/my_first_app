from logging import PlaceHolder
from flask import Flask
from flask.helpers import url_for
from markupsafe import escape
from flask import render_template
from flask import request
from flask import session
from flask import redirect
import random
import eventlet


from flask_socketio import SocketIO
from flask_socketio import join_room, leave_room

from flask_sqlalchemy import SQLAlchemy
import sqlite3
import json

app = Flask(__name__)
app.secret_key = 'meme'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
socket = SocketIO(app)

db = SQLAlchemy(app)


class Room(db.Model):
   id = db.Column(db.Integer, primary_key=True)
   key = db.Column(db.String, nullable=False, unique=True)
   status = db.Column(db.String)
   
   def __repr__(self):
       return '<room {}>'.format(self.id)

class User(db.Model):
   id = db.Column(db.Integer, primary_key=True)
   name = db.Column(db.String, nullable=False, unique=True)
   fk_room = db.Column(db.Integer, db.ForeignKey('room.id'), nullable = True)
   role = db.Column(db.String, nullable=True)
   pick_name_to = db.Column(db.Integer, db.ForeignKey('user.id'))
   ready = db.Column(db.Boolean)
   character = db.Column(db.String)
   
   def __repr__(self):
       return '<room {}>'.format(self.id)


@app.route("/")
def index():

    user_id = session.get('user_id')
    if user_id:
        
        user = User.query.filter_by(id = user_id).first()
        print(user.fk_room)

        if user.fk_room:
            return redirect(url_for('room_page', room_id = user.fk_room))
        else:
            return redirect(url_for('create_or_join_room'))
    else:
        return redirect(url_for('login'))


@app.route("/login", methods = ['GET', 'POST'])
def login():
    if request.method == 'POST':

        new_user = User(
            name = request.form['name'],
            ready = False
        )

        db.session.add(new_user)
        db.session.commit()

        session['user_id'] = new_user.id

        return redirect(url_for('index'))

    else:
        return render_template('login-form.html')

@app.route("/create-or-join-room", methods = ['GET'])
def create_or_join_room():
    return render_template(
        'create-or-join-room.html',
        create_endpoint = url_for('create_new_room'),
        join_endpoint = url_for('join_existing_room')
        )

@app.route('/create-room', methods=['POST'])
def create_new_room():

    new_room = Room(
        key = request.form.get('room_key'),
        status = 'Open'
    )

    user_id = session.get('user_id')
    try:
        #criar nova sala
        db.session.add(new_room)
        db.session.commit()

    except Exception as e:
        print(e)
        return "Error creating room"
    
    user = User.query.filter_by(id = user_id).first()
    user.fk_room = new_room.id
    user.role = 'Host'
    db.session.commit()

    session['user_role'] = user.role
    session['room_id'] = new_room.id

    return redirect(url_for('room_page', room_id = new_room.id))

@app.route('/join-room', methods=['POST'])
def join_existing_room():
    
    room = Room.query.filter_by(key=request.form['room_key']).first()

    if room:
        user = User.query.filter_by(id = session['user_id']).first()
        user.fk_room = room.id
        user.role = 'Guest'
        db.session.commit()

        session['user_role'] = user.role
        session['room_id'] = room.id
    
    else:
        return "Room does not exist"

    return redirect(url_for('room_page', room_id = room.id))


@app.route('/room/<room_id>')
def room_page(room_id):
    return render_template('room.html', room_id = room_id, user_role = session['user_role'], user_id = session['user_id'])

@app.route('/reset')
def reset():
    session.clear()
    return redirect(url_for('index'))

@socket.on('join_room')
def handle_join():

    user = User.query.filter_by(id = session['user_id']).first()
    room = Room.query.filter_by(id = user.fk_room).first()
    join_room(room.id)
    users = User.query.filter_by(fk_room = room.id)

    print(room.status)
    if room.status == 'Open' or room.status == 'Closed':
        doc = render_template('lobby.html', users = users)
    elif room.status == 'Character picking':
        doc = render_template('pick-character.html', users = user)
    elif room.status == 'In match':
        doc = render_template('match.html', users = users)

    socket.emit('game_update', data = {'doc':doc}, to=room.id)

@socket.on('start_game')
def handle_start_game():
  
    #Mudar o statud da sala
    room = Room.query.filter_by(id = session['room_id']).first()
    room.status = 'Character picking'
    db.session.commit()

    #Definir os pick_name_to
    users = User.query.filter_by(fk_room = room.id)

    rolls = [{'user': user, 'roll':random.randint(1,20)} for user in users]
    rolls.sort(key=lambda x: x['roll'])

    last_user = rolls[-1]['user'].id
    for roll in rolls:
        roll['user'].pick_name_to = last_user
        last_user = roll['user'].id
    db.session.commit()

    doc = render_template('pick-character.html')

    socket.emit('game_update', data = {'doc':doc}, to = room.id)

@socket.on('pick_character')
def handle_pick_character(data):
    
    user = User.query.filter_by(id = session['user_id']).first()
    user_to_pick_name = User.query.filter_by(id = user.pick_name_to).first()

    user.ready = True
    user_to_pick_name.character = data['character']
    db.session.commit()

    all_users_in_room = User.query.filter_by(fk_room = user.fk_room)

    all_users_ready = True
    for u in all_users_in_room:
        if not u.ready:
            all_users_ready = False
            break
    
    if all_users_ready:
        room = Room.query.filter_by(id = user.fk_room).first()
        room.status = 'In match'
        
        for u in all_users_in_room:
            user.ready = False

        db.session.commit()

        doc = render_template('match.html', users = all_users_in_room)
        socket.emit('game_update', data = {'doc': doc}, to = user.fk_room)

@socket.on('correct_guess')
def handle_correct_guess():
    user = User.query.filter_by(id = session['user_id']).first()
    user.ready = True
    db.session.commit()

    all_users_in_room = User.query.filter_by(fk_room = user.fk_room)

    all_users_ready = True
    for u in all_users_in_room:
        if not u.ready:
            all_users_ready = False
            break
    
    if all_users_ready:
        room = Room.query.filter_by(id = user.fk_room).first()
        room.status = 'Open'

        for u in all_users_in_room:
            u.ready = False

        db.session.commit()

        doc = render_template('lobby.html', users = all_users_in_room)
        socket.emit('game_update', data = {'doc': doc}, to = user.fk_room)

if __name__ == '__main__':
    # Threaded option to enable multiple instances for multiple user access support
    socket.run(app, debug=False)






