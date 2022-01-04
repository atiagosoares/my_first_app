from . import db
from .models import User, Room, Match, MatchPlayerInfo
from datetime import datetime

def get_game_info(room_id):

    room = Room.query.filter_by(id = room_id).first()
    print(room)

    info = {
        'room_id' : room.id,
        'room_key' : room.key,
        'room_status' : room.status,
        'users': []
    }

    # Player ID
    # Players Ifo
    users = User.query.filter_by(fk_room = room.id)

    for user in users:
        info['users'].append({
            'id' : user.id,
            'name' : user.name
        })

    # Match Info
    match = Match.query.filter_by(fk_room = room_id, in_progress=True).first()

    if match:
        match_info = {
            'id' : match.id,
            'match_player_info' : []
        }

        match_player_info = MatchPlayerInfo.query.filter_by(fk_match=match.id)
        for line in match_player_info:
            match_info['match_player_info'].append({
                'fk_user' : line.fk_user,
                'pick_character_to' : line.pick_character_to,
                'character': line.character
            })
        info['match_info'] = match_info
    return info

def remove_user_from_room(user):
    #Change db values
    user.fk_room = None
    user.role = None
    db.session.commit()

    # We can't remove the user session data or the user from the socketio room from his id.
    # We'll deal with that in anoter ways

def end_match(match):
    match.in_progress = False
    match.status = "Ended"
    match.match_ended_at = datetime.now()
    db.session.commit()
