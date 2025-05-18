from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from datetime import datetime, timedelta

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///wallet.db'
app.config['JWT_SECRET_KEY'] = 'super-secret'

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    balance = db.Column(db.Float, default=0.0)

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    amount = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    type = db.Column(db.String(10))
    flagged = db.Column(db.Boolean, default=False)

def detect_fraud(user_id, amount, type):
    now = datetime.utcnow()
    recent = Transaction.query.filter_by(sender_id=user_id).filter(Transaction.timestamp > now - timedelta(minutes=1)).count()
    if recent > 3 or amount > 10000:
        return True
    return False

@app.route('/', methods=['GET'])
def index():
    return jsonify(message='Digital Wallet API is running')

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    hashed_pw = bcrypt.generate_password_hash(data['password']).decode('utf-8')
    user = User(username=data['username'], password_hash=hashed_pw)
    db.session.add(user)
    db.session.commit()
    return jsonify(message='User registered'), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    user = User.query.filter_by(username=data['username']).first()
    if user and bcrypt.check_password_hash(user.password_hash, data['password']):
        token = create_access_token(identity=user.id)
        return jsonify(token=token)
    return jsonify(message='Invalid credentials'), 401

@app.route('/deposit', methods=['POST'])
@jwt_required()
def deposit():
    user_id = get_jwt_identity()
    data = request.json
    amount = data['amount']
    if amount <= 0:
        return jsonify(message='Invalid deposit amount'), 400
    user = User.query.get(user_id)
    user.balance += amount
    flagged = detect_fraud(user_id, amount, 'deposit')
    txn = Transaction(sender_id=user_id, amount=amount, type='deposit', flagged=flagged)
    db.session.add(txn)
    db.session.commit()
    return jsonify(message='Deposit successful')

@app.route('/withdraw', methods=['POST'])
@jwt_required()
def withdraw():
    user_id = get_jwt_identity()
    data = request.json
    amount = data['amount']
    user = User.query.get(user_id)
    if amount <= 0 or user.balance < amount:
        return jsonify(message='Invalid withdrawal'), 400
    user.balance -= amount
    flagged = detect_fraud(user_id, amount, 'withdraw')
    txn = Transaction(sender_id=user_id, amount=amount, type='withdraw', flagged=flagged)
    db.session.add(txn)
    db.session.commit()
    return jsonify(message='Withdrawal successful')

@app.route('/transfer', methods=['POST'])
@jwt_required()
def transfer():
    user_id = get_jwt_identity()
    data = request.json
    recipient = User.query.filter_by(username=data['to']).first()
    amount = data['amount']
    sender = User.query.get(user_id)
    if not recipient or amount <= 0 or sender.balance < amount:
        return jsonify(message='Invalid transfer'), 400
    sender.balance -= amount
    recipient.balance += amount
    flagged = detect_fraud(user_id, amount, 'transfer')
    txn = Transaction(sender_id=user_id, receiver_id=recipient.id, amount=amount, type='transfer', flagged=flagged)
    db.session.add(txn)
    db.session.commit()
    return jsonify(message='Transfer successful')

@app.route('/transactions', methods=['GET'])
@jwt_required()
def get_transactions():
    user_id = get_jwt_identity()
    txns = Transaction.query.filter((Transaction.sender_id == user_id) | (Transaction.receiver_id == user_id)).all()
    return jsonify([{
        'id': t.id,
        'type': t.type,
        'amount': t.amount,
        'timestamp': t.timestamp.isoformat(),
        'flagged': t.flagged
    } for t in txns])

@app.route('/admin/flags', methods=['GET'])
@jwt_required()
def get_flagged():
    txns = Transaction.query.filter_by(flagged=True).all()
    return jsonify([{
        'id': t.id,
        'sender_id': t.sender_id,
        'amount': t.amount,
        'type': t.type
    } for t in txns])

@app.route('/admin/stats', methods=['GET'])
@jwt_required()
def get_stats():
    users = User.query.all()
    total_balance = sum(user.balance for user in users)
    top_users = sorted(users, key=lambda x: x.balance, reverse=True)[:5]
    return jsonify({
        'total_balance': total_balance,
        'top_users': [{'username': u.username, 'balance': u.balance} for u in top_users]
    })

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
