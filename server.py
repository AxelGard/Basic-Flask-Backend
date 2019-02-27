from flask import Flask, session, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
import random, json, os
from flask_jwt_extended import (
    JWTManager, jwt_required, get_jwt_identity,
    create_access_token, get_raw_jwt
)


if 'NAMESPACE' in os.environ and os.environ['NAMESPACE'] == 'heroku':
    db_uri = os.environ['DATABASE_URL']
    debug_flag = False
else: # when running locally with sqlite
    db_path = os.path.join(os.path.dirname(__file__), 'app.db')
    db_uri = 'sqlite:///{}'.format(db_path)
    debug_flag = True

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'SecretKey'
app.config['JWT_BLACKLIST_ENABLED'] = True
app.config['JWT_BLACKLIST_TOKEN_CHECKS'] = ['access']
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = 3600*24*7 # A week

jwt = JWTManager(app)
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)


readby = db.Table('readby',
    db.Column('msg_id',db.Integer, db.ForeignKey("message.msg_id"), primary_key = True),
    db.Column('user_id',db.Integer, db.ForeignKey("user.user_id"), primary_key = True)
)


class User(db.Model):
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80))
    psw_hash = db.Column(db.LargeBinary())

    def __init__(self, username, password):
        self.username = username
        self.psw_hash = bcrypt.generate_password_hash(password)

    def to_dict(self):
        return {'username': username, 'password': password}

class Message(db.Model):
    msg_id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.Text)
    read_by = db.relationship('User', secondary=readby)


class Blacklist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    jti = db.Column(db.String(36), nullable=False)

    def __init__(self, jti):
        self.jti = jti


def start_app():
    db.drop_all()
    db.create_all()


@app.route("/")
@app.route("/home")
def home():
    """ basic start page """
    return "<h1> Home page </h1>"


@app.route("/messages/<MessageID>/flag/<UserId>", methods=["POST"])
@jwt_required
def mark_as_read(MessageID, UserId):
    """ marks msg as read """
    UserId = make_id_int(UserId)
    MessageID = make_id_int(MessageID)
    msg = Message.query.filter_by(msg_id=MessageID).first()
    user = User.query.filter_by(user_id=UserId).first()
    if not msg:
        return abort(400)
    if not user:
        return abort(400)
    msg.read_by.append(user)
    db.session.commit()
    return "Message marked as read", 200



@app.route("/messages", methods=["POST", "GET"])
def print_or_save_msg():
    """
    prints out all messages if calld on with GET
    and if called with POST saves given msg
    """
    if request.method == "GET":
        return print_msgs()
    else:
        return save_msg()


@app.route("/messages/unread/<UserId>", methods=["GET"])
@jwt_required
def unread_msg(UserId):
    """ Shows all messages UserId has not read """
    UserId = make_id_int(UserId)
    result = []
    message_table = Message.query.all()
    for msg in message_table:
        if not UserId in [user.user_id for user in msg.read_by]:
            dict = {'id': msg.msg_id, 'message': msg.message,
                    'readBy': [user.user_id for user in msg.read_by]}
            result.append(dict)
    return json.dumps(result)


@app.route("/messages/<MessageID>", methods=["GET", "DELETE"])
def get_or_delete_msg(MessageID):
    """ Gets a message if GET and deletes message if DELETE"""
    if request.method == "GET":
        return fetch_msg(MessageID)
    else:
        return delete_msg(MessageID)

@jwt.token_in_blacklist_loader
def check_if_token_in_blacklist(decrypted_token):
    jti = decrypted_token['jti']
    token = Blacklist.query.filter_by(jti = jti).first()
    return token != None


@app.route("/user/login", methods=["POST"])
def login():
    username = request.form.get('username')
    password = request.form.get('password')

    user = User.query.filter_by(username = username).first()

    if (user == None):
        abort(401)

    if bcrypt.check_password_hash(user.psw_hash, password):
        access_token = create_access_token(identity=username)
        dict = {'access_token': access_token}
        return json.dumps(dict), 200
    abort(401)


@app.route("/user/logout", methods=["POST"])
@jwt_required
def logout():
    jti = get_raw_jwt()['jti']
    blacklist = Blacklist(jti)
    db.session.add(blacklist)
    db.session.commit()
    return jsonify({"msg": "Successfully logged out"}), 200


@app.route("/user", methods=["POST"])
def create_user():
    username = request.form.get('username')
    password = request.form.get('password')

    user = User.query.filter_by(username = username).first()
    #password = bcrypt.generate_password_hash(password).decode('utf-8')
    if user != None:
        return jsonify({"msg": "user already exists"}), 400
    user = User(username, password)
    db.session.add(user)
    db.session.commit()
    return jsonify({"msg": "user registered"}), 200


def fetch_msg(MessageID):
    """ returns the msg with MessageID """
    MessageID = make_id_int(MessageID)
    message = Message.query.filter_by(msg_id=MessageID).first()
    if not message:
        return abort(400)
    dict = {'id': message.msg_id, 'message': message.message,
            'readBy': [user.user_id for user in message.read_by]}
    return json.dumps(dict), 200


@jwt_required
def delete_msg(MessageID):
    """ removes a msg """
    MessageID = make_id_int(MessageID)
    message = Message.query.filter_by(msg_id=MessageID).first()
    if not message:
        return abort(400)
    db.session.delete(message)
    db.session.commit()
    return "Message deleted", 200


@jwt_required
def save_msg():
    """ Creates and saves a new message """
    msg = request.form.get('message')
    if not msg or len(msg) > 140:
        return abort(400)
    message = Message(message=msg)
    db.session.add(message)
    db.session.commit()
    return json.dumps({"id": message.msg_id})


def print_msgs():
    """ returns whole data base server """
    result = []
    message_table = Message.query.all()
    for message in message_table:
        result.append({'id': message.msg_id, 'message': message.message,
                'readBy': [user.user_id for user in message.read_by]})
    return json.dumps(result)

def make_id_int(id):
    try:
        return int(id)
    except ValueError:
        return abort(400)

if __name__ == '__main__':
    start_app()
    if not ('NAMESPACE' in os.environ and os.environ['NAMESPACE'] == 'heroku'):
        app.run(debug=True, port=4040)
