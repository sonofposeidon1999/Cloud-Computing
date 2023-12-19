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
app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
res=app.test_client()
ip_addr="http://54.165.131.117"
ip_addr_orch="http://54.165.205.180"
headers={"Content-Type":"application/json"}

#API:1
@app.route('/api/v1/users', methods=['PUT'])
def create_user():
	print("in users")
	data = request.get_json(force=True)
	pattern = re.compile(r'\b[0-9a-f]{40}\b')
	if(bool(pattern.match(data['password']))!=True):
		abort(400)
	req=requests.post(ip_addr_orch+"/api/v1/db/write", json={"api":"1","name":data['username'],"password":data['password']}, headers={"Origin":"54.165.131.117"})
	if(req.json()=="True"):
		status_code = flask.Response(status=201)
		return status_code
	else:
		abort(400)
#API:2
@app.route('/api/v1/users/<string:username>', methods=['DELETE'])
def remove_user(username):
	req=requests.post(ip_addr_orch+"/api/v1/db/write", json ={"api":"2","name":username},headers={"Origin":"54.165.131.117"})
	if(req.json()=="True"):
		status_code = flask.Response(status=201)
		return status_code
	else:
		abort(400)

@app.route('/api/v1/users', methods=['GET'])
def list_all_users():
	with app.test_client() as client:
		response = client.get('/')
		if response.status_code==405:
			abort(str(response.status_code))
	r= requests.post(ip_addr_orch+"/api/v1/db/read",json={"api":"10"},headers={"Origin":"54.165.131.117"})
	a=r.json()
	a=a.split(",")
	if(len(a)!=0):
		if(a[0][0]=='\"'):
			a[0]=a[0][1:]
		if(a[-1][-1]=='\"'):
			a[-1]=a[-1][0:-1]
	if len(a)>0:
		return json.dumps(a),200
	elif len(a)==0:
		return 204
	else:
		return 400

if __name__ == '__main__':
	app.run(host='0.0.0.0',port=80,debug=True)
