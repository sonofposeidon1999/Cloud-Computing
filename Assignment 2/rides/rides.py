import os
from flask import Flask, request, jsonify, make_response
from flask import render_template, redirect, url_for, abort
from flask_sqlalchemy import SQLAlchemy
import uuid
from werkzeug.security import generate_password_hash, check_password_hash
import datetime
from functools import wraps
from sqlalchemy import Column, Integer, DateTime
import re
import requests
import json
import pandas as pd

count=0
df=pd.read_csv("locdb.csv")
d=dict(zip(df['Area No'],df['Area Name']))
app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
res=app.test_client()
app.config['SECRET_KEY'] = 'thisissecret'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'tutorial.db')
db = SQLAlchemy(app)
headers={"Content-Type":"application/json"}
class MyDateTime(db.TypeDecorator):
	impl = db.DateTime
	def process_bind_param(self, value, dialect):
		if type(value) is str:
			return datetime.datetime.strptime(value, '%d-%m-%Y:%S-%M-%H')
		return value

#CREATING USER
class User(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(50))
	password = db.Column(db.String(80))

#CREATING RIDER
class Rider(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	created_by = db.Column(db.String(50))
	timestamp = db.Column(MyDateTime, default=datetime.datetime.now)
	source = db.Column(db.Integer)
	destination = db.Column(db.Integer)

class Shared(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	ride_id = db.Column(db.Integer)
	shared_by = db.Column(db.String(50))


#API:3
@app.route('/api/v1/rides', methods=['POST'])
def create_rider():
	global count
	count+=1
	data = request.get_json(force=True)
	df=list()
	message = requests.get("http://user:8080/api/v1/users",json={},headers=headers)
	#return message.text
	for x in message.text[1:-1].split(', '):
		df.append(x[1:-1])
	#return str(df[1])
	if request.method == 'POST':
		if data['created_by'] in df:
			requests.post(request.url_root+"api/v1/db/write", json ={"api":"3","created_by":data['created_by'], "timestamp":data['timestamp'], "source":data['source'], "destination":data['destination']},headers=headers)
			return {},201
		else:
			return "user does not exist"
	else:
		abort(405)

#API:4
@app.route('/api/v1/rides', methods=['GET'])
def upcoming_rides():
	with app.test_client() as client:
		response = client.get('/')
		if response.status_code==405:
			abort(str(response.status_code))
	global count
	count+=1
	source=request.args.get('source')
	destination=request.args.get('destination')
	read_data = requests.post(request.url_root+"api/v1/db/read",json={"api":"4"})
	read_data = read_data.json()
	# return jsonify(read_data)
	upcoming = []
	current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
	current_time = datetime.datetime.now().strptime(current_time,"%Y-%m-%d %H:%M:%S")
	for i in range(len(read_data["created_by"])):
		time1 = datetime.datetime.strptime(read_data['timestamp'][i],"%a, %d %b %Y %H:%M:%S %Z" )
		if(source == read_data['source'][i] and destination == read_data['destination'][i] and time1>current_time):
			time1 = datetime.strptime(read_data['timestamp'][i],"%a, %d %b %Y %H:%M:%S %Z" )
			time = datetime.strftime(time1,"%d-%m-%Y:%S-%M-%H")
			upcoming.append({"rideId":read_data['rideId'][i],"username":read_data['created_by'][i],"timestamp":time})
	if(len(upcoming)!=0):
		return jsonify(upcoming),200
	elif(len(upcoming)==0):
		return {},204
	else:
		abort(400)


#API:5,6,7
@app.route('/api/v1/rides/<int:ride_id>',methods=['GET','DELETE','POST'])
def list_ride(ride_id):
	global count
	count+=1
	if request.method == 'GET':
		if db.session.query(Rider).filter_by(id=ride_id).count():
			r=requests.post(request.url_root+"api/v1/db/read", json ={"api":"5","ride_id":ride_id},headers=headers)
			return r.json(),200
		else:
			return {},204
	elif request.method == 'POST':
		df=list()
		message = requests.get("http://user:8080/api/v1/users",json={},headers=headers)
		#return message.text
		for x in message.text[1:-1].split(', '):
			df.append(x[1:-1])
		#return str(df)
		#return request.get_json(force=True)['username']
		if db.session.query(Rider).filter_by(id=ride_id).count() and request.get_json(force=True)['username'] in df:
			requests.post(request.url_root+"api/v1/db/write", json ={"api":"6","ride_id":ride_id,"shared_by":request.get_json(force=True)['username']},headers=headers)
			return {},201
		else:
			return jsonify("Ride not identified && sharer not found")
	elif request.method == 'DELETE':
		if db.session.query(Rider).filter_by(id=ride_id).count():
			requests.post(request.url_root+"api/v1/db/write",json={"api":"7","ride_id":ride_id})
			return {},200
		else:
			return {},204
	else:
		abort(405)

#API:8
@app.route('/api/v1/db/write', methods=['POST'])
def write_db():
	global count
	count+=1
	data = request.get_json(force=True)
	if(data['api']=="3"):
		new_rider= Rider( created_by=data['created_by'], timestamp=data['timestamp'], source=data['source'], destination=data['destination'])
		db.session.add(new_rider)
		db.session.commit()
	if(data['api']=="6"):
		new_shared = Shared(ride_id=data['ride_id'],shared_by=data['shared_by'])
		db.session.add(new_shared)
		db.session.commit()
	if(data['api']=="7"):
		rider_delete= db.session.query(Rider).filter_by(id=data['ride_id']).one()
		db.session.delete(rider_delete)
		db.session.commit()
#API:9
@app.route('/api/v1/db/clear',methods=['POST'])
def clear_db():
	global count
	count+=1
	meta = db.metadata
	for table in reversed(meta.sorted_tables):
		session.execute(table.delete())
	session.commit()
	return {},200

@app.route('/api/v1/db/read', methods=['POST'])
def read_db():
	data = request.get_json(force=True)
	global count
	count+=1
	if(data['api']=="4"):
		read_data = db.session.query(Rider).all()
		ride_data = dict()
		ride_data['rideId'] = []
		ride_data['created_by'] = []
		ride_data['timestamp'] = []
		ride_data['source'] = []
		ride_data['destination'] = []
		for ride in read_data:
			ride_data['rideId'].append(ride.id)
			ride_data['created_by'].append(ride.created_by)
			ride_data['timestamp'].append(ride.timestamp)
			ride_data['source'].append(ride.source)
			ride_data['destination'].append(ride.destination)
		return ride_data
	if(data['api']=="5"):
		ride = db.session.query(Rider).filter_by(id=data['ride_id']).one()
		shared = db.session.query(Shared).filter_by(ride_id=data['ride_id']).all()
		l=[]
		for share in shared:
			l.append(share.shared_by)
		return jsonify(ride_Id=ride.id,Created_by=ride.created_by,users=l,Timestamp=ride.timestamp,source=d[ride.source],destination=d[ride.destination])

#API:10
@app.route('/api/v1/_count', methods=['GET','DELETE'])
def count_user():
	global count
	if request.method == 'GET':
		return json.dumps(count)
	if request.method == 'DELETE':
		count=0
		return {},200
	if request.method not in ['GET','DELETE']:
		return {},405

def list_all_users():
	root = str(request.url_root)[:-3]+"80/"
	return requests.get("http://user:8080/api/v1/users")

if __name__ == '__main__':
	app.run(host='0.0.0.0',port=8000,debug=True)
