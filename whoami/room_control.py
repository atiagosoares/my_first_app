from . import socket, db
from .models import User, Room, Match, MatchPlayerInfo
from .helpers import get_game_info, end_match, remove_user_from_room
from flask_socketio import join_room, leave_room
from flask import session, Blueprint
from datetime import datetime


@socket.on('connect')
def handle_connect():

    user = User.query.filter_by(id = session['user_id']).first()
    join_room(user.fk_room)

    game_info = get_game_info(user.fk_room)
    print(game_info)

    socket.emit('user_connected', data = game_info, to=user.fk_room)

def terminate_room(room):
    #Room can be terminated from any status
    if room.status != "Terminated":
        room.status = "Terminated"
        db.session.commit()
    
    #Any ongoing matches are ended
    matches = Match.query.filter_by(fk_room = room.id, in_progress = True)
    for match in matches:
        end_match(match)
    
    #Users are removed from room
    users = User.query.filter_by(fk_room = room.id)
    for user in users:
        remove_user_from_room(user)
    
    socket.emit('room_terminated', to = room.id)

def remove_user_from_room(user):
    
    # If there was a match in progress when the user left
    # Also remove the user from the match

    match = Match.query.filter_by(fk_room = user.fk_room, in_progress = True).first()

    if match:
        mpi = MatchPlayerInfo.query.filter_by(fk_match = match.id, fk_user = user.id).first()
        db.session.delete(mpi)
    
    user.role = None
    user.fk_room = None

    db.session.commit()


@socket.on('leave_room')
def handle_leave():

    user = User.query.filter_by(id = session['user_id']).first()
    leave_room(user.fk_room)

    room = Room.query.filter_by(id = user.fk_room).first()

    if user.role == 'Host':
        # For now, room is terminated if host leaves. I could also swaps this to a change host function
        terminate_room(room)

    else:
        remove_user_from_room(user)

        game_info = get_game_info(room.id)
        socket.emit('user_disconnected', data = game_info, to=user.fk_room)

@socket.on('disconnect')
def handle_disconnect():

    user = User.query.filter_by(id = session['user_id']).first()
    leave_room(user.fk_room)

    game_info = get_game_info(user.fk_room)
    
    socket.emit('user_disconnected', data = game_info, to=user.fk_room)


@socket.on('close_room')
def handle_close_room():

    room_id = session.get("room_id")
    room = Room.query.filter_by(id = room_id).first()

    # Room status can only change to "Closed" while "Open"
    if room.status == "Open":
        room.status = "Closed"
        db.session.commit()

    game_info = get_game_info(room_id)

    socket.emit('room_closed', data = game_info, to = room.id)

@socket.on('open_room')
def handle_open_room():
    room_id = session.get("room_id")
    room = Room.query.filter_by(id = room_id).first()

    # Room status can only change to "Open" while "Closed"
    if room.status == "Closed":
        room.status = "Open"
        db.session.commit()

    game_info = get_game_info(room_id)

    socket.emit('room_opened', data = game_info, to = room.id)


@socket.on("terminate_room")
def handle_terminate_room():

    room_id = session.get("room_id")
    room = Room.query.filter_by(id = room_id).first()

    terminate_room(room)
    
@socket.on("end_match")
def handle_end_match():

    room_id = session.get("room_id")
    room = Room.query.filter_by(id = room_id).first()

    # Room can only have a match ended if it's on the Picking Phase or Guessing Phase
    if room.status == "Picking Phase" or room.status == "Guessing Phase":

        #There should be a match in progress...
        match = Match.query.filter_by(fk_room = room_id, in_progress = True).first()
        if match:
            end_match(match)