@socket.on('connect')
def handle_connect():

    user = User.query.filter_by(id = session['user_id']).first()
    join_room(user.fk_room)

    game_info = get_game_info(user.fk_room)
    print(game_info)

    socket.emit('game_update', data = game_info, to=user.fk_room)

@socket.on('disconnect')
def handle_disconnect():

    user = User.query.filter_by(id = session['user_id']).first()
    leave_room(user.fk_room)

    game_info = get_game_info(user.fk_room)

    socket.emit('game_update', data = game_info, to=user.fk_room)


@socket.on('close_room')
def handle_close_room():

    room_id = session.get("room_id")
    room = Room.query.filter_by(id = room_id).first()

    # Room status can only change to "Closed" while "Open"
    if room.status == "Open":
        room.status = "Closed"
        db.session.commit()

    game_info = get_game_info(room_id)

    socket.emit('game_update', data = game_info, to = room.id)

@socket.on('open_room')
def handle_open_room():
    room_id = session.get("room_id")
    room = Room.query.filter_by(id = room_id).first()

    # Room status can only change to "Open" while "Closed"
    if room.status == "Closed":
        room.status = "Open"
        db.session.commit()

    game_info = get_game_info(room_id)

    socket.emit('game_update', data = game_info, to = room.id)

def remove_user_from_room(user):

    #Change db values
    user.fk_room = None
    user.role = None
    db.session.commit()

    # We can't remove the user session data or the user from the socketio room from his id.
    # We'll deal with that in anoter ways

@socket.on("terminate_room")
def handle_terminate_room():

    room_id = session.get("room_id")
    room = Room.query.filter_by(id = room_id).first()

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
    
    socket.emit('terminate', to = room.id)

def end_match(match):
    match.in_progress = False
    match.status = "Ended"
    match.match_ended_at = datetime.now()
    db.session.commit()
    
@socket.on("end_match")
def handle_end_match():

    room_id = session.get("room_id")
    room = Room.query.filter_by(id = room_id).first()

    # Room can only have a match ended if it's on the Picking Phase or Guessing Phase
    if room.status == "Picking Phase" or room.status == "Guessing Phase":
        
        #Get current match in progress; match can only end while in progress
        room.status = "Closed" # Room defaults to closed state

        #There should be a match in progress...
        match = Match.query.filter_by(fk_room = room_id, in_progress = True).first()
        if match:
            end_match(match)
        
        db.session.commit()

    game_info = get_game_info(room.id)

    socket.emit('game_update', data = game_info, to = room.id)