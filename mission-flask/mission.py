from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from os import environ

from datetime import datetime

app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = environ.get('dbURL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_recycle': 299}

db = SQLAlchemy(app)

CORS(app)


class Mission(db.Model):
    __tablename__ = 'missions'

    mission_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    description = db.Column(db.String(256), nullable=False)
    difficulty = db.Column(db.String(64), nullable=False)
    duration = db.Column(db.Float(precision=2), nullable=False)
    award_points = db.Column(db.Integer, nullable=False)
    is_active = db.Column(db.Boolean, default=False, nullable=False)
    created = db.Column(db.DateTime, nullable=False, default=datetime.now)
    modified = db.Column(db.DateTime, nullable=False,
                         default=datetime.now, onupdate=datetime.now)

    def __init__(self, name, description, difficulty, duration, award_points, is_active):
        self.name = name
        self.description = description
        self.difficulty = difficulty
        self.duration = duration
        self.award_points = award_points
        self.is_active = is_active

    def json(self):
        return {"mission_id": self.mission_id, "name": self.name, "description": self.description, "difficulty": self.difficulty, "duration": self.duration, "award_points": self.award_points, "is_active": self.is_active, "created": self.created, "modified": self.modified}


with app.app_context():
    db.create_all()
    existing_mission_1 = db.session.query(Mission).filter(Mission.mission_id==1).first()
    if not existing_mission_1:
        new_mission_1 = Mission(name="Are you afraid of the mummy?", description="Ride Revenge of the Mummy 5 times to gain 500 points!", difficulty="Medium", duration=5.0, award_points=500, is_active=1)
        new_mission_2 = Mission(name="Get wet at Jurassic Park Rapids Adventure!", description="Ride Jurassic Park Rapids Adventure 10 times to gain 1000 points!", difficulty="Easy", duration=5.0, award_points=1000, is_active=1)
        new_mission_3 = Mission(name="Go on an adventure with Puss in Boots!", description="Ride Puss in Boots Journey 3 times to gain 100 points!", difficulty="Easy", duration=2.0, award_points=100, is_active=1)
        db.session.add(new_mission_1)
        db.session.add(new_mission_2)
        db.session.add(new_mission_3)
        db.session.commit()



@app.route("/mission")
def get_all():
    missionlist = Mission.query.all()
    if len(missionlist):
        return jsonify(
            {
                "code": 200,
                "data": {
                    "missions": [mission.json() for mission in missionlist]
                }
            }
        ), 200
    return jsonify(
        {
            "code": 404,
            "message": "There are no missions."
        }
    ), 404


@app.route("/mission/active")
def get_active_missions():
    activemissionlist = Mission.query.filter_by(is_active=True).all()
    if len(activemissionlist):
        return jsonify(
            {
                "code": 200,
                "data": {
                    "missions": [mission.json() for mission in activemissionlist]
                }
            }
        ), 200
    return jsonify(
        {
            "code": 404,
            "message": "There are no active missions."
        }
    ), 404


@app.route("/mission/<mission_id>")
def find_by_mission_id(mission_id):
    mission = Mission.query.filter_by(mission_id=mission_id).first()
    if mission:
        return jsonify(
            {
                "code": 200,
                "data": mission.json()
            }
        ), 200
    return jsonify(
        {
            "code": 404,
            "message": "Mission not found."
        }
    ), 404


@app.route("/mission", methods=['POST'])
def create_mission():
    data = request.get_json()
    mission = Mission(**data)

    existing_mission = Mission.query.filter_by(name=mission.name).first()

    if (existing_mission):
        return jsonify(
            {
                "code": 400,
                "data": {
                    "mission_id": existing_mission.mission_id
                },
                "message": "Mission already exists."
            }
        ), 400

    try:
        db.session.add(mission)
        db.session.commit()
    except:
        return jsonify(
            {
                "code": 500,
                "message": "An error occurred creating the mission."
            }
        ), 500

    return jsonify(
        {
            "code": 201,
            "data": mission.json()
        }
    ), 201


@app.route("/mission/<mission_id>", methods=['PUT'])
def update_mission(mission_id):
    if (not Mission.query.filter_by(mission_id=mission_id).first()):
        return jsonify(
            {
                "code": 404,
                "data": {
                    "mission_id": mission_id
                },
                "message": "Mission not found."
            }
        ), 404

    mission = Mission.query.filter_by(mission_id=mission_id).first()
    data = request.get_json()

    try:
        mission.name = data['name']
        mission.description = data['description']
        mission.difficulty = data['difficulty']
        mission.duration = data['duration']
        mission.award_points = data['award_points']
        mission.is_active = data['is_active']
        db.session.commit()

    except:
        return jsonify(
            {
                "code": 500,
                "data": {
                    "mission_id": mission_id
                },
                "message": "An error occurred updating the mission."
            }
        ), 500

    return jsonify(
        {
            "code": 200,
            "data": mission.json()
        }
    ), 200


@app.route("/mission/<mission_id>", methods=['DELETE'])
def delete_mission(mission_id):
    if (not Mission.query.filter_by(mission_id=mission_id).first()):
        return jsonify(
            {
                "code": 404,
                "data": {
                    "mission_id": mission_id
                },
                "message": "Mission not found."
            }
        ), 404

    mission = Mission.query.filter_by(mission_id=mission_id).first()

    try:
        db.session.delete(mission)
        db.session.commit()
    except:
        return jsonify(
            {
                "code": 500,
                "data": {
                    "mission_id": mission_id
                },
                "message": "An error occurred deleting the mission."
            }
        ), 500

    return jsonify(
        {
            "code": 200,
            "message": "Mission with ID " + mission_id + " successfully deleted."
        }
    ), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=6300, debug=True)
