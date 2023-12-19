
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
import flask
#count of read requests
dic ={"count" :0} 
with open("count.json", "w") as outfile: 
    json.dump(dic, outfile) 

df=pd.read_csv("locdb.csv")
d=dict(zip(df['Area No'],df['Area Name']))
app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
res=app.test_client()
app.config['SECRET_KEY'] = 'thisissecret'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'tutorial.db')
db = SQLAlchemy(app)
ip_addr="http://3.218.27.77"
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
	data = request.get_json(force=True)
	if db.session.query(User).filter_by(name=data['username']).count():
		abort(400)
	pattern = re.compile(r'\b[0-9a-f]{40}\b')
	if(bool(pattern.match(data['password']))!=True):
		abort(400)
	requests.post(ip_addr+"/api/v1/db/write", json={"api":"1","name":data['username'],"password":data['password']},headers=headers)
	status_code = flask.Response(status=201)
	return status_code

#API:2
@app.route('/api/v1/users/<string:username>', methods=['DELETE'])
def remove_user(username):
	if db.session.query(User).filter_by(name=username).count():
		requests.post(ip_addr+"/api/v1/db/write", json ={"api":"2","name":username})
		status_code = flask.Response(status=201)
		return status_code	
	else:
		abort(400)

#API:9
@app.route('/api/v1/users', methods=['GET'])
def list_all_users():
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
	if(data['api']=="1"):
		new_user = User(name=data['name'], password=data['password'])
		db.session.add(new_user)
		db.session.commit()
	if(data['api']=="2"):
		user_delete= db.session.query(User).filter_by(name=data['name']).one()
		db.session.delete(user_delete)
		db.session.commit()
	with open("count.json", "r") as jsonFile:
	    data = json.load(jsonFile)
	data["count"] =data["count"]+1
	with open("count.json", "w") as jsonFile:
	    json.dump(data, jsonFile)

@app.route('/api/v1/db/clear',methods=['POST'])
def clear_db():
	meta = db.metadata
	for table in reversed(meta.sorted_tables):
		db.session.execute(table.delete())
	db.session.commit()
	return {},200

@app.route('/api/v1/_count',methods=['GET'])
def count():
	with open("count.json", "r") as jsonFile:
	    data = json.load(jsonFile)
	return jsonify(data["count"])

@app.route('/api/v1/_count',methods=['DELETE'])
def reset_count():
	with open("count.json", "r") as jsonFile:
	    data = json.load(jsonFile)
	data["count"] =0
	with open("count.json", "w") as jsonFile:
	    json.dump(data, jsonFile)
	status_code = flask.Response(status=201)
	return status_code
if __name__ == '__main__':
	app.run(host='0.0.0.0',port=80,debug=True)
