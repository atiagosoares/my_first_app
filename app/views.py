from app import app

@app.route("/")
def index():
    user_id = session.get('user_id')
    if user_id:
        user = User.query.filter_by(id = user_id).first()

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
            user_created_at = datetime.now()
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

    return redirect(url_for('room_page', room_id = new_room.id))

@app.route('/join-room', methods=['POST'])
def join_existing_room():
    
    room = Room.query.filter_by(id=request.form['room_id']).first()

    if room.key == request.form['room_key']:
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