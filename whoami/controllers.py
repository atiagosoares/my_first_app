from flask import Blueprint, session, redirect, request, render_template
from flask.helpers import url_for

from datetime import datetime

from whoami.models import User, Room

from whoami import app, db

con = Blueprint('con', __name__)

@con.route("/")
def index():
    user_id = session.get('user_id')
    if user_id:
        user = User.query.filter_by(id = user_id).first()

        if user.fk_room:
            return redirect(url_for('con.room_page', room_id = user.fk_room))
        else:
            return redirect(url_for('con.create_or_join_room'))
    else:
        return redirect(url_for('con.login'))


@con.route("/login", methods = ['GET', 'POST'])
def login():
    if request.method == 'POST':

        new_user = User(
            name = request.form['name'],
            user_created_at = datetime.now()
        )

        db.session.add(new_user)
        db.session.commit()

        session['user_id'] = new_user.id

        return redirect(url_for('con.index'))

    else:
        return render_template('login-form.html')

@con.route("/create-or-join-room", methods = ['GET'])
def create_or_join_room():
    return render_template(
        'create-or-join-room.html',
        create_endpoint = url_for('con.create_new_room'),
        join_endpoint = url_for('con.join_existing_room')
        )

@con.route('/create-room', methods=['POST'])
def create_new_room():

    new_room = Room(
        key = request.form.get('room_key'),
        status = 'Open',
        room_created_at = datetime.now()
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

    return redirect(url_for('con.room_page', room_id = new_room.id))

@con.route('/join-room', methods=['POST'])
def join_existing_room():
    
    room = Room.query.filter_by(id=request.form['room_id']).first()

    if not room:
        return "Room does not exist"
    
    elif room.status != "Open":
        return "Room is not open"

    if room.key == request.form['room_key']:
        user = User.query.filter_by(id = session['user_id']).first()
        user.fk_room = room.id
        user.role = 'Guest'
        db.session.commit()

        session['user_role'] = user.role
        session['room_id'] = room.id
    
    else:
        return "Wrong key"

    return redirect(url_for('con.room_page', room_id = room.id))


@con.route('/room/<room_id>')
def room_page(room_id):
    return render_template('room.html', room_id = room_id, user_role = session['user_role'], user_id = session['user_id'])

@con.route('/reset')
def reset():
    session.clear()
    return redirect(url_for('con.index'))

from . import room_control, game_events