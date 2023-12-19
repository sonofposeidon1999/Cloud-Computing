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

#API:1
@app.route('/api/v1/users', methods=['PUT'])
def create_user():
	global count
	count+=1
	with app.test_client() as client:
		response = client.get('/')
		if response.status_code==405:
			abort(str(response.status_code))
	data = request.get_json(force=True)
	if db.session.query(User).filter_by(name=data['username']).count():
		return {'user exists'}
		#abort(400)
	pattern = re.compile(r'\b[0-9a-f]{40}\b')
	if(bool(pattern.match(data['password']))!=True):
		password 
		abort(400)
	requests.post(request.url_root+"api/v1/db/write", json={"api":"1","name":data['username'],"password":data['password']},headers=headers)
	return {},201

#API:2
@app.route('/api/v1/users/<string:username>', methods=['DELETE'])
def remove_user(username):
	global count
	count+=1
	with app.test_client() as client:
		response = client.get('/')
		if response.status_code==405:
			abort(str(response.status_code))
	if db.session.query(User).filter_by(name=username).count():
		requests.post(request.url_root+"api/v1/db/write", json ={"api":"2","name":username})
		return {},200
	else:
		abort(204)

#API:9
@app.route('/api/v1/users', methods=['GET'])
def list_all_users():
	global count
	count+=1
	with app.test_client() as client:
		response = client.get('/')
		if response.status_code==405:
			abort(str(response.status_code))
	read_data = db.session.query(User).all()
	user_data = []
	for user in read_data:
		user_data.append(user.name)
	if len(user_data)>0:
		return json.dumps(user_data),200
	elif len(user_data)==0:
		return 204
	else:
		return 400

#API:8
@app.route('/api/v1/db/write', methods=['POST'])
def write_db():
	data = request.get_json(force=True)
	global count
	count+=1
	if(data['api']=="1"):
		new_user = User(name=data['name'], password=data['password'])
		db.session.add(new_user)
		db.session.commit()
	if(data['api']=="2"):
		user_delete= db.session.query(User).filter_by(name=data['name']).one()
		db.session.delete(user_delete)
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

if __name__ == '__main__':
	app.run(host='0.0.0.0',port=8080,debug=True)
