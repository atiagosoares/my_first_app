from . import socket, db
from .models import User, Room, Match, MatchPlayerInfo
from .helpers import get_game_info, end_match

from flask import session
from datetime import datetime

import random

@socket.on('start_match')
def handle_start_match():
  
    # Mudar o status da sala
    room = Room.query.filter_by(id = session['room_id']).first()
    room.status = 'Picking Phase'
    db.session.commit()

    #Inicar nova partida
    new_match = Match(
        fk_room = room.id,
        match_started_at = datetime.now(),
        match_status = "Picking Phase"
    )

    db.session.add(new_match)
    db.session.commit()

    # Identificar os usuários atualmente na sala
    users = User.query.filter_by(fk_room = room.id)

    # Fazer um shuffle aleatório
    rolls = [{'player': player, 'roll':random.randint(1,20)} for player in users]
    rolls.sort(key=lambda x: x['roll'])

    # Adicionar jogadores na partida
    last_player = rolls[-1]['player']
    for roll in rolls:
        new_player = MatchPlayerInfo(
                fk_match = new_match.id, 
                fk_user = roll['player'].id,
                pick_character_to = last_player.id
            )

        db.session.add(new_player)
        last_player = roll['player']
    db.session.commit()

    game_info = get_game_info(room.id)

    socket.emit('match_started', data = game_info, to = room.id)

def end_match(match):
    match.in_progress = False
    match.status = "Ended"
    match.match_ended_at = datetime.now()

    room = Room.query.filter_by(id = match.fk_room).first()
    room.status = "Closed"

    db.session.commit()

    game_info = get_game_info(room.id)
    socket.emit("match_ended", data = game_info, to = room.id)


def advance_to_guessing_phase(match):

    match.status = "Guessing Phase"
    match.guessing_phase_started_at = datetime.now()
    db.session.commit()

    game_info = get_game_info(match.fk_room)
    socket.emit("advanced_to_guessing_phase", data = game_info, to = match.fk_room)

@socket.on('pick_character')

def handle_pick_character(data):

    room = Room.query.filter_by(id = session.get('room_id')).first()
    match = Match.query.filter_by(fk_room = room.id, in_progress=True).first()

    player_info = MatchPlayerInfo.query.filter_by(fk_match = match.id, fk_user = session['user_id']).first()
    player_to_set_char = MatchPlayerInfo.query.filter_by(fk_match = match.id, fk_user = player_info.pick_character_to).first()

    player_info.picked_character_at = datetime.now()
    player_to_set_char.character = data['character']
    db.session.commit()

    all_users_in_match = MatchPlayerInfo.query.filter_by(fk_match = match.id)

    all_users_ready = True
    for u in all_users_in_match:
        if not u.character:
            all_users_ready = False
            break
    
    if all_users_ready:
        room = Room.query.filter_by(id = room.id).first()
        room.status = 'Guessing Phase'
        db.session.commit()

        advance_to_guessing_phase(match)

def check_if_all_players_guessed(match):
    all_users_in_match = MatchPlayerInfo.query.filter_by(fk_match = match.id)

    all_users_guessed = True
    for u in all_users_in_match:
        if not u.guessed_character_at:
            all_users_guessed = False
            break
    
    return all_users_guessed

@socket.on('correct_guess')
def handle_correct_guess():

    room = Room.query.filter_by(id = session.get('room_id')).first()
    match = Match.query.filter_by(fk_room = room.id, in_progress=True).first()

    player_info = MatchPlayerInfo.query.filter_by(fk_match = match.id, fk_user = session['user_id']).first()
    player_info.guessed_character_at = datetime.now()
    db.session.commit()

    all_users_guessed = check_if_all_players_guessed(match)
    
    if all_users_guessed:
        end_match(match)