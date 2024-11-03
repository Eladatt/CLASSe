from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import random

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///fun_platform.db'
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    riddle = db.Column(db.String(200), nullable=False)
    answer = db.Column(db.String(80), nullable=False)
    score = db.Column(db.Integer, default=0)

class Riddle(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    riddle = db.Column(db.String(200), nullable=False)
    answer = db.Column(db.String(80), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    user = User(username=data['username'], riddle=data['riddle'], 
                answer=generate_password_hash(data['answer']))
    db.session.add(user)
    db.session.commit()
    return jsonify({'message': 'Registration successful'})

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    user = User.query.filter_by(username=data['username']).first()
    if user and check_password_hash(user.answer, data['answer']):
        login_user(user)
        return jsonify({'message': 'Login successful'})
    return jsonify({'message': 'Invalid credentials'}), 401

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return jsonify({'message': 'Logged out successfully'})

@app.route('/create_riddle', methods=['POST'])
@login_required
def create_riddle():
    data = request.json
    riddle = Riddle(riddle=data['riddle'], answer=data['answer'], user_id=current_user.id)
    db.session.add(riddle)
    current_user.score += 10
    db.session.commit()
    return jsonify({'message': 'Riddle created successfully'})

@app.route('/get_crossword')
@login_required
def get_crossword():
    riddles = Riddle.query.order_by(db.func.random()).limit(5).all()
    crossword = generate_crossword([r.answer for r in riddles])
    return jsonify({
        'crossword': crossword,
        'clues': [r.riddle for r in riddles]
    })

@app.route('/leaderboard')
def leaderboard():
    users = User.query.order_by(User.score.desc()).limit(10).all()
    return jsonify([{'username': u.username, 'score': u.score} for u in users])

def generate_crossword(words):
    # Implement a simple crossword generation algorithm
    # This is a placeholder and should be replaced with a more sophisticated algorithm
    crossword = [
        "  " + words[0],
        "  " + words[0][1],
        words[1] + words[0][2],
        "  " + words[1][1] + " " + words[2],
        "  " + words[1][2]
    ]
    return crossword

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
def seed_riddles():
    placeholder_riddles = [
        ("I speak without a mouth and hear without ears. I have no body, but I come alive with wind. What am I?", "Echo"),
        ("You measure my life in hours and I serve you by expiring. I'm quick when I'm thin and slow when I'm fat. The wind is my enemy. What am I?", "Candle"),
        ("I have cities, but no houses. I have mountains, but no trees. I have water, but no fish. What am I?", "Map"),
        ("What has keys, but no locks; space, but no room; you can enter, but not go in?", "Keyboard"),
        ("I am taken from a mine and shut up in a wooden case, from which I am never released, and yet I am used by everyone. What am I?", "Pencil lead")
    ]
    
    for riddle, answer in placeholder_riddles:
        if not Riddle.query.filter_by(riddle=riddle).first():
            new_riddle = Riddle(riddle=riddle, answer=answer, user_id=1)
            db.session.add(new_riddle)
    
    db.session.commit()

# Call this function after creating the database
with app.app_context():
    db.create_all()
    seed_riddles()