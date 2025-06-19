from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import os

# Delete existing DB if it exists
if os.path.exists("candidate_dashboard.db"):
    os.remove("candidate_dashboard.db")

app = Flask(__name__)
CORS(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///candidate_dashboard.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    profile_completeness = db.Column(db.Integer, default=0)

class TrainingWishlist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    training_name = db.Column(db.String(120), nullable=False)

class JobMatchingProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    job_title = db.Column(db.String(120), nullable=False)

# Utility
def get_current_user():
    user_id = request.args.get('user_id', type=int)
    if not user_id:
        return None
    return User.query.filter_by(id=user_id).first()

# Routes
@app.route('/')
def index():
    return jsonify({
        "message": "Welcome to the Candidate Dashboard",
        "endpoints": [
            "GET /dashboard/profile_completeness?user_id=1",
            "GET /dashboard/training_wishlist?user_id=1",
            "GET /dashboard/jobs_matching_profile?user_id=1",
            "GET /users",
            "POST /user",
            "PUT /user/<id>",
            "POST /training_wishlist",
            "POST /job_matching_profile"
        ]
    })

@app.route('/users', methods=['GET'])
def list_users():
    users = User.query.all()
    return jsonify([{
        "id": u.id,
        "username": u.username,
        "profile_completeness": u.profile_completeness
    } for u in users])

@app.route('/dashboard/profile_completeness', methods=['GET'])
def profile_completeness():
    user = get_current_user()
    if not user:
        return jsonify({"error": "User not found or no user_id provided"}), 404
    return jsonify({
        "username": user.username,
        "profile_completeness": f"{user.profile_completeness}%"
    })

@app.route('/dashboard/training_wishlist', methods=['GET'])
def training_wishlist():
    user = get_current_user()
    if not user:
        return jsonify({"error": "User not found or no user_id provided"}), 404
    trainings = TrainingWishlist.query.filter_by(user_id=user.id).all()
    trainings_list = [t.training_name for t in trainings]
    return jsonify({
        "username": user.username,
        "wishlist_count": len(trainings_list),
        "trainings": trainings_list
    })

@app.route('/dashboard/jobs_matching_profile', methods=['GET'])
def jobs_matching_profile():
    user = get_current_user()
    if not user:
        return jsonify({"error": "User not found or no user_id provided"}), 404
    if user.profile_completeness < 50:
        return jsonify({
            "message": "Complete your profile to see matching jobs.",
            "profile_completeness": f"{user.profile_completeness}%"
        }), 403
    jobs = JobMatchingProfile.query.filter_by(user_id=user.id).all()
    jobs_list = [j.job_title for j in jobs]
    return jsonify({
        "username": user.username,
        "matching_jobs_count": len(jobs_list),
        "matching_jobs": jobs_list
    })

@app.route('/user', methods=['POST'])
def create_user():
    data = request.get_json()
    username = data.get('username')
    if not username:
        return jsonify({"error": "Username is required"}), 400
    if User.query.filter_by(username=username).first():
        return jsonify({"error": "Username already exists"}), 400
    user = User(username=username, profile_completeness=data.get('profile_completeness', 0))
    db.session.add(user)
    db.session.commit()
    return jsonify({"message": "User created", "user_id": user.id}), 201

@app.route('/user/<int:id>', methods=['PUT'])
def update_user(id):
    user = User.query.get(id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    data = request.get_json()
    user.profile_completeness = data.get('profile_completeness', user.profile_completeness)
    db.session.commit()
    return jsonify({"message": "User updated"})

@app.route('/training_wishlist', methods=['POST'])
def add_training():
    data = request.get_json()
    user_id = data.get('user_id')
    training_name = data.get('training_name')
    if not (user_id and training_name):
        return jsonify({"error": "user_id and training_name are required"}), 400
    wishlist = TrainingWishlist(user_id=user_id, training_name=training_name)
    db.session.add(wishlist)
    db.session.commit()
    return jsonify({"message": "Training added to wishlist"})

@app.route('/job_matching_profile', methods=['POST'])
def add_job():
    data = request.get_json()
    user_id = data.get('user_id')
    job_title = data.get('job_title')
    if not (user_id and job_title):
        return jsonify({"error": "user_id and job_title are required"}), 400
    job = JobMatchingProfile(user_id=user_id, job_title=job_title)
    db.session.add(job)
    db.session.commit()
    return jsonify({"message": "Job added to matching profile"})

# 404 handler
@app.errorhandler(404)
def page_not_found(e):
    return jsonify({"error": "This route does not exist"}), 404

# Run app
if __name__ == '__main__':
    with app.app_context():
        db.drop_all()
        db.create_all()
        print("💾 Database recreated. Inserting sample data...")

        users = [
            User(username="alice", profile_completeness=20),
            User(username="bob", profile_completeness=55),
            User(username="carol", profile_completeness=70),
            User(username="dave", profile_completeness=90),
            User(username="eve", profile_completeness=40),
        ]
        db.session.add_all(users)
        db.session.commit()

        trainings = [
            TrainingWishlist(user_id=1, training_name="Python Basics"),
            TrainingWishlist(user_id=2, training_name="Flask Advanced"),
            TrainingWishlist(user_id=3, training_name="Data Science 101"),
            TrainingWishlist(user_id=4, training_name="Machine Learning"),
            TrainingWishlist(user_id=5, training_name="Cybersecurity Essentials"),
        ]
        db.session.add_all(trainings)

        jobs = [
            JobMatchingProfile(user_id=2, job_title="Backend Developer"),
            JobMatchingProfile(user_id=3, job_title="Data Analyst"),
            JobMatchingProfile(user_id=4, job_title="ML Engineer"),
            JobMatchingProfile(user_id=4, job_title="DevOps Engineer"),
            JobMatchingProfile(user_id=3, job_title="BI Developer"),
        ]
        db.session.add_all(jobs)
        db.session.commit()

    app.run(debug=True, port=5050)
