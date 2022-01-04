def get_game_info(room_id):

    # Room ID
    # Room KEY
    # Room status

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

    socket.emit('game_update', data = game_info, to = room.id)



def advance_to_guessing_phase(match):

    match.status = "Guessing Phase"
    match.guessing_phase_started_at = datetime.now()

    db.session.commit()

@socket.on('pick_character')

def handle_pick_character(data):

    room = Room.query.filter_by(id = session.get('room_id')).first()
    match = Match.query.filter_by(fk_room = room.id, in_progress=True).first()

    player_info = MatchPlayerInfo.query.filter_by(fk_user = session['user_id']).first()
    player_to_set_char = MatchPlayerInfo.query.filter_by(fk_match = match.id, pick_character_to = player_info.pick_character_to).first()

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
    
    game_info = get_game_info(room.id)
    socket.emit('game_update', data = game_info, to = room.id)

@socket.on('correct_guess')
def handle_correct_guess():

    room = Room.query.filter_by(id = session.get('room_id')).first()
    match = Match.query.filter_by(fk_room = room.id, in_progress=True).first()

    player_info = MatchPlayerInfo.query.filter_by(fk_match = match.id, fk_user = session['user_id']).first()
    player_info.guessed_character_at = datetime.now()
    db.session.commit()

    all_users_in_match = MatchPlayerInfo.query.filter_by(fk_match = match.id)

    all_users_guessed = True
    for u in all_users_guessed:
        if not u.guessed_character_at:
            all_users_ready = False
            break
    
    if all_users_ready:

        room.status = "Closed"
        db.session.commit()

        end_match(match)

    game_info = get_game_info(room.id)    
    socket.emit('game_update', data = game_info, to = room.id)