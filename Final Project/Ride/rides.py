#!/usr/bin/env python
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
ip_addr="http://52.21.31.137"
df=pd.read_csv("locdb.csv")
d=dict(zip(df['Area No'],df['Area Name']))
app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
res=app.test_client()
headers={"Content-Type":"application/json"}
ip_addr_orch="http://54.165.205.180"
#API:3
@app.route('/api/v1/rides', methods=['POST'])
def create_rider():
	data = request.get_json(force=True)
	req=requests.post(ip_addr_orch + "/api/v1/db/write", json ={"api":"3","created_by":data['created_by'], "timestamp":data['timestamp'], "source":data['source'], "destination":data['destination']},headers={"Origin":"52.21.31.137"})
	if(req.json()=="True"):
		status_code = flask.Response(status=201)
		return status_code
	else:
		abort(400)

#API:4
@app.route('/api/v1/rides', methods=['GET'])
def upcoming_rides():
	with app.test_client() as client:
		response = client.get('/')
		if response.status_code==405:
			abort(str(response.status_code))
	source=int(request.args.get('source'))
	destination=int(request.args.get('destination'))
	if(source<1 and soruce>198 and destination<1 and destination>198):
		status_code = flask.Response(status=204)
		return status_code
	read_data1 = requests.post(ip_addr_orch+"/api/v1/db/read",json={"api":"4"},headers={"Origin":"52.21.31.137"})
	read_data1 = read_data1.json()
	read_data={}
	s=[i.split(",") for i in read_data1.split(";")]
	if(s[0]==''):
		status_code = flask.Response(status=204)
		return status_code	
	s[0][0]=s[0][0][1:]
	s[-1][-1]=s[-1][-1][:-1]
	s[0]=[int(i) for i in s[0]]
	s[3]=[int(i) for i in s[3]]
	s[4]=[int(i) for i in s[4]]
	read_data['rideId']=s[0]
	read_data['created_by']=s[1]
	read_data['timestamp']=s[2]
	read_data['source']=s[3]
	read_data['destination']=s[4]
	upcoming = []
	current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
	current_time = datetime.datetime.now().strptime(current_time,"%Y-%m-%d %H:%M:%S")
	for i in range(len(read_data["created_by"])):
		time1 = datetime.datetime.strptime(read_data['timestamp'][i],"%d-%m-%Y:%H-%M-%S" )
		if(source == read_data['source'][i] and destination == read_data['destination'][i] and time1>current_time):
			time1 = datetime.datetime.strptime(read_data['timestamp'][i],"%d-%m-%Y:%H-%M-%S" )
			time = datetime.datetime.strftime(time1,"%d-%m-%Y:%S-%M-%H")
			upcoming.append({"rideId":read_data['rideId'][i],"username":read_data['created_by'][i],"timestamp":time})
	if(len(upcoming)!=0):
		return jsonify(upcoming),200
	elif(len(upcoming)==0):
		status_code = flask.Response(status=204)
		return status_code
	else:
		abort(400)

#API:5,6,7
@app.route('/api/v1/rides/<int:ride_id>',methods=['GET','DELETE','POST'])
def list_ride(ride_id):
	print("Get")
	if request.method == 'GET':
		r=requests.post(ip_addr_orch+"/api/v1/db/read", json ={"api":"5","ride_id":str(ride_id)},headers={"Origin":"52.21.31.137"})
		r=r.json()
		s=r.split(";")
		if(len(s[0])>1):
			s[0]=s[0][1:]
		else:	
			status_code = flask.Response(status=204)
			return status_code
		if(s[2]=='Empty'):
			s[2]=[]
		else:
			s[2]=s[2].split(":")
		s[0]=int(s[0])
		s[4]=int(s[4])
		s[4]=d[s[4]]
		s[5]=int(s[5])
		s[5]=d[s[5]]
		ride_data={}
		ride_data['rideId']=s[0]
		ride_data['created_by']=s[1]
		ride_data['users']=s[2]
		ride_data['timestamp']=s[3]
		ride_data['source']=s[4]
		ride_data['destination']=s[5]
		return jsonify(ride_data)
	elif request.method == 'POST':
		req=requests.post(ip_addr_orch+"/api/v1/db/write", json ={"api":"6","ride_id":str(ride_id),"shared_by":request.get_json(force=True)['username']},headers={"Origin":"52.21.31.137"})
		if(req.json()=="True"):
			status_code = flask.Response(status=200)
			return status_code
		else:
			status_code = flask.Response(status=204)
			return status_code

	elif request.method == 'DELETE':
		req=requests.post(ip_addr_orch+"/api/v1/db/write", json ={"api":"7","ride_id":str(ride_id)},headers={"Origin":"52.21.31.137"})
		if(req.json()=="True"):
			status_code = flask.Response(status=200)
			return status_code
		else:
			abort(400)
if __name__ == '__main__':
	app.run(host='0.0.0.0',port=80,debug=True)
