class Room(db.Model):
   id = db.Column(db.Integer, primary_key=True)
   key = db.Column(db.String, nullable=False)
   status = db.Column(db.String)
   room_created_at = db.Column(db.DateTime, nullable=False)
   
   def __repr__(self):
       return '<room {}>'.format(self.id)

class User(db.Model):
   id = db.Column(db.Integer, primary_key=True)
   name = db.Column(db.String, nullable=False)
   fk_room = db.Column(db.Integer, db.ForeignKey('room.id'), nullable = True)
   user_type = db.Column(db.String, nullable=False, default="Guest User")
   user_status = db.Column(db.String, nullable=False, default="Connected")
   role = db.Column(db.String, nullable=True)
   user_created_at = db.Column(db.DateTime, nullable=False)
   
   def __repr__(self):
       return '<room {}>'.format(self.id)

class MatchPlayerInfo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fk_match = db.Column(db.Integer, db.ForeignKey('match.id'), nullable = False)
    fk_user = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    pick_character_to = db.Column(db.Integer, db.ForeignKey('user.id'), nullable = True)
    character = db.Column(db.String, nullable = True)
    picked_character_at = db.Column(db.DateTime, nullable = True)
    guessed_character_at = db.Column(db.DateTime, nullable = True)
    gave_up_at = db.Column(db.DateTime, nullable=True)

class Match(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fk_room = db.Column(db.Integer, db.ForeignKey('room.id'), nullable = True)
    in_progress = db.Column(db.Boolean, nullable = False, default = True)
    match_status = db.Column(db.String, nullable=False)
    match_started_at = db.Column(db.DateTime, nullable = False)
    match_guess_phase_started_at = db.Column(db.DateTime, nullable = True)
    match_ended_at = db.Column(db.DateTime, nullable = True)