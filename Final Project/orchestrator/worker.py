#!/usr/bin/env python
import pika
import json
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
import sys
import sqlite3
import threading
import flask

ip_addr="http://3.220.27.213"
app = Flask(__name__)
#con = sqlite3.connect('tutorial.db')





#READ
def callbackread(ch, method, props, body):
	data = json.loads(body)
	response={}
	users=[]
	#API:4
	if(data['api']=="4"):
		ride_data = dict()
		ride_data['rideId'] = []
		ride_data['created_by'] = []
		ride_data['timestamp'] = []
		ride_data['source'] = []
		ride_data['destination'] = []
		query="SELECT id,created_by,timestamp,source,destination FROM rider"
		with sqlite3.connect(path_slave) as con:
			cur=con.cursor()
			cur.execute(query)
			con.commit()
		for i in cur:
			ride_data['rideId'].append(str(i[0]))
			ride_data['created_by'].append(i[1])
			ride_data['timestamp'].append(i[2])
			ride_data['source'].append(str(i[3]))
			ride_data['destination'].append(str(i[4]))
		response=";".join([",".join(i) for i in ride_data.values()])

	#API:5
	if(data['api']=="5"):
		query="SELECT * FROM rider where id='"+data["ride_id"]+"'"
		with sqlite3.connect(path_slave) as con:
			cur=con.cursor()
			cur.execute(query)
			con.commit()
		ride_details=cur.fetchone()
		query="SELECT * FROM shared where ride_id='"+data["ride_id"]+"'"
		with sqlite3.connect(path_slave1) as con:
			cur=con.cursor()
			cur.execute(query)
			con.commit()
		shared_details=cur.fetchall()
		l=[]
		for share in shared_details:
			l.append(share[2])
		if(len(l)==0):
			l.append("Empty")
		l=":".join(l)
		print("List of users ",l)
		response=str(ride_details[0])+";"+ride_details[1]+";"+l+";"+ride_details[2]+";"+ride_details[3]+";"+ride_details[4]+";"
		'''response['ride_Id']=ride_details[0]
		response['Created_by']=ride_details[1]
		response['users']=l
		response['Timestamp']=ride_details[2]
		response['source']=int(ride_details[3])
		response['destination']=int(ride_details[4])'''
		print(response)
	#API:10
	if(data['api']=="10"):
		query="select * from users"
		with sqlite3.connect(path_slave) as con:
			cur=con.cursor()
			cur.execute(query)
			con.commit()
		for i in cur:
			users.append(i[1])
		response=",".join(users)
	print(response)
	ch.queue_declare(queue='responseQ',durable = True)
	ch.basic_publish(exchange='',
	    routing_key=props.reply_to,
	    properties=pika.BasicProperties(correlation_id =props.correlation_id,content_type='application/json',),
	    body=json.dumps(response))

	ch.basic_ack(delivery_tag = method.delivery_tag)


#WRITE
def callbackwrite(ch, method, props, body):
	print("writing start")
	data = json.loads(body)
	response=True
	#API:1
	if(data['api']=="1"):
		user_get_query="select * from users where name='"+data['name']+"'"
		with sqlite3.connect(path_master) as con:
			cur=con.cursor()
			cur.execute(user_get_query)
			con.commit()
		if(len(cur.fetchall())==0):
			user_insert_query="INSERT INTO users(name,password) VALUES ('"+data['name']+"','"+data['password']+"')"
			with sqlite3.connect(path_master) as con:
				cur=con.cursor()
				cur.execute(user_insert_query)
				con.commit()   
			with sqlite3.connect(temp_db) as con:
				cur=con.cursor()
				cur.execute(user_insert_query)
				con.commit()
			connection = pika.BlockingConnection(
			pika.ConnectionParameters(host='rmq'))
			channel = connection.channel()
			channel.exchange_declare(exchange='logs', exchange_type='fanout')
			channel.basic_publish(exchange='logs', routing_key='', body=str(user_insert_query),properties=pika.BasicProperties(delivery_mode=2,))
			print("new user inserted successfully")
		else:
			response=False
			print("new user inserted unsuccessfully")
	#API:2
	if(data['api']=="2"):
		user_get_query="select * from users where name='"+data['name']+"'"
		with sqlite3.connect(path_master) as con:
			cur=con.cursor()
			cur.execute(user_get_query)
			con.commit()
		if(len(cur.fetchall())!=0):
			user_delete_query="DELETE FROM users WHERE name='"+data['name']+"'"
			with sqlite3.connect(path_master) as con:
				cur=con.cursor()
				cur.execute(user_delete_query)
				con.commit()
			with sqlite3.connect(temp_db) as con:
				cur=con.cursor()
				cur.execute(user_delete_query)
				con.commit() 
			connection = pika.BlockingConnection(
			pika.ConnectionParameters(host='rmq'))
			channel = connection.channel()
			channel.exchange_declare(exchange='logs', exchange_type='fanout')
			channel.basic_publish(exchange='logs', routing_key='', body=str(user_delete_query),properties=pika.BasicProperties(delivery_mode=2,))
			print("user deleted successfully")
		else:
			response=False
			print("new user inserted unsuccessfully")
	#API:3
	if(data['api']=="3"):
		user_insert_query="select * from users where name='"+data['created_by']+"'"
		with sqlite3.connect(path_master) as con:
			cur=con.cursor()
			cur.execute(user_insert_query)
			con.commit()
		if(len(cur.fetchall())!=0):
			rider_insert_query="INSERT INTO rider(created_by,timestamp,source,destination) VALUES ('"+data['created_by']+"','"+data['timestamp']+"','"+str(data['source']) +"','"+str(data['destination'])+"')"
			with sqlite3.connect(path_master) as con:
				cur=con.cursor()
				cur.execute(rider_insert_query)
				con.commit()
			with sqlite3.connect(temp_db) as con:
				cur=con.cursor()
				cur.execute(rider_insert_query)
				con.commit()
			connection = pika.BlockingConnection(
			pika.ConnectionParameters(host='rmq'))
			channel = connection.channel()
			channel.exchange_declare(exchange='logs', exchange_type='fanout')
			channel.basic_publish(exchange='logs', routing_key='', body=str(rider_insert_query),properties=pika.BasicProperties(delivery_mode=2,))
			print("new rider inserted successfully")
		else:
			response=False
			print("new user inserted unsuccessfully")
	#API:6
	if(data['api']=="6"):
		user_insert_query="select * from users where name='"+data['shared_by']+"'"
		with sqlite3.connect(path_master) as con:
			user=con.cursor()
			user.execute(user_insert_query)
			con.commit()
		user_insert_query="select * from rider where id='"+data['ride_id']+"'"
		with sqlite3.connect(path_master) as con:
			ride=con.cursor()
			ride.execute(user_insert_query)
			con.commit()
		if(len(user.fetchall())!=0 and len(ride.fetchall())!=0):
			shared_insert_query="INSERT INTO shared(ride_id,shared_by) VALUES ('"+str(data['ride_id'])+"','"+str(data['shared_by'])+"')"
			with sqlite3.connect(path_master) as con:
				cur=con.cursor()
				cur.execute(shared_insert_query)
				con.commit()   
			with sqlite3.connect(temp_db) as con:
				cur=con.cursor()
				cur.execute(shared_insert_query)
				con.commit()    
			connection = pika.BlockingConnection(
			pika.ConnectionParameters(host='rmq'))
			channel = connection.channel()
			channel.exchange_declare(exchange='logs', exchange_type='fanout')
			channel.basic_publish(exchange='logs', routing_key='', body=str(shared_insert_query),properties=pika.BasicProperties(delivery_mode=2,))
			print("user inserted successfully")
		else:
			response=False
			print("new user inserted unsuccessfully")
	#API:7
	if(data['api']=="7"):
		user_insert_query="select * from rider where id="+data['ride_id']
		with sqlite3.connect(path_master) as con:
			ride=con.cursor()
			ride.execute(user_insert_query)
			con.commit()
		if(len(ride.fetchall())!=0):
			rider_delete_query="DELETE FROM rider where id="+data['ride_id']
			with sqlite3.connect(path_master) as con:
				cur=con.cursor()
				cur.execute(rider_delete_query)
				con.commit()
			with sqlite3.connect(temp_db) as con:
				cur=con.cursor()
				cur.execute(rider_delete_query)
				con.commit()
			connection = pika.BlockingConnection(
			pika.ConnectionParameters(host='rmq'))
			channel = connection.channel()
			channel.exchange_declare(exchange='logs', exchange_type='fanout')
			channel.basic_publish(exchange='logs', routing_key='', body=str(rider_delete_query),properties=pika.BasicProperties(delivery_mode=2,))
			print("rider deleted successfully")
		else:
			response=False
			print("new user inserted unsuccessfully")

	if(data['api']=="11"):
		rider_delete_query="DELETE FROM rider"
		with sqlite3.connect(path_master) as con:
			cur=con.cursor()
			cur.execute(rider_delete_query)
			con.commit()
		with sqlite3.connect(temp_db) as con:
			cur=con.cursor()
			cur.execute(rider_delete_query)
			con.commit()
		rider_delete_query="DELETE FROM users"
		with sqlite3.connect(path_master) as con:
			cur=con.cursor()
			cur.execute(rider_delete_query)
			con.commit()
		with sqlite3.connect(temp_db) as con:
			cur=con.cursor()
			cur.execute(rider_delete_query)
			con.commit()
			connection = pika.BlockingConnection(
			pika.ConnectionParameters(host='rmq'))
			channel = connection.channel()
			channel.exchange_declare(exchange='logs', exchange_type='fanout')
			channel.basic_publish(exchange='logs', routing_key='', body=str("delete all"),properties=pika.BasicProperties(delivery_mode=2,))
		print("ALL records deleted successfully")
	ch.basic_publish(exchange='',
	    routing_key=props.reply_to,
	    properties=pika.BasicProperties(correlation_id =props.correlation_id,),
	    body=str(response))

	ch.basic_ack(delivery_tag = method.delivery_tag)


#SYNC
def callbacksync(ch, method, props, body):
	data = body.decode()
	print(data)
	if(data!="delete all"):
		with sqlite3.connect(path_slave) as con:
			cur=con.cursor()
			cur.execute(data)
			con.commit()
	else:
		data="DELETE FROM rider"
		with sqlite3.connect(path_slave) as con:
			cur=con.cursor()
			cur.execute(data)
			con.commit()
		data="DELETE FROM users"
		with sqlite3.connect(path_slave) as con:
			cur=con.cursor()
			cur.execute(data)
			con.commit()

	print("sync done")
	ch.basic_ack(delivery_tag = method.delivery_tag)


#SLAVE
if(sys.argv[1]=='slave'):
	print("In slave")
	cont_id = os.popen("hostname").read().strip()
	path_slave=cont_id+".db"
	sql_create_users_table = "CREATE TABLE IF NOT EXISTS users (id integer PRIMARY KEY,name text NOT NULL,password text);"
	sql_create_rider_table = "CREATE TABLE IF NOT EXISTS rider (id integer PRIMARY KEY,  created_by text,timestamp text, source text,destination text);"
	sql_create_shared_table = "CREATE TABLE IF NOT EXISTS shared (id integer PRIMARY KEY,ride_id text,shared_by text);"
	with sqlite3.connect(path_slave) as con:
		cur=con.cursor()
		cur.execute(sql_create_users_table)
		cur.execute(sql_create_rider_table)
		cur.execute(sql_create_shared_table)
		con.commit()
	try:
		master_path="master.db"
		sql_master_ride = "SELECT * FROM rider;"
		with sqlite3.connect(master_path) as con:
			ride=con.cursor()
			ride.execute(sql_master_ride)
			con.commit()
		ride_data=ride.fetchall()
		sql_master_user = "SELECT * FROM users;"
		with sqlite3.connect(master_path) as con:
			user=con.cursor()
			user.execute(sql_master_user)
			con.commit()
		user_data=user.fetchall()
		for i in ride_data:
			rider_insert_query="INSERT INTO rider(created_by,timestamp,source,destination) VALUES ('"+i[1]+"','"+i[2]+"','"+str(i[3])+"','"+str(i[4])+"')"
			with sqlite3.connect(path_slave) as con:
				user=con.cursor()
				user.execute(rider_insert_query)
				con.commit()
		for i in user_data:
			user_insert_query="INSERT INTO users(name,password) VALUES ('"+i[1]+"','"+i[2]+"')"
			with sqlite3.connect(path_slave) as con:
				user=con.cursor()
				user.execute(user_insert_query)
				con.commit()
	except Exception as e:
		print(e)
	#syncQ
	def s():
		connection = pika.BlockingConnection(
		pika.ConnectionParameters(host='rmq'))
		channel = connection.channel()
		channel.exchange_declare(exchange='logs', exchange_type='fanout')
		result = channel.queue_declare(queue='', exclusive=True)
		queue_name = result.method.queue
		channel.queue_bind(exchange='logs', queue=queue_name)
		print(' [*] Updating the slave database.')
		channel.basic_qos(prefetch_count=1)
		channel.basic_consume(queue=queue_name, on_message_callback=callbacksync)
		channel.start_consuming()
	#readQ
	def r():
		connection = pika.BlockingConnection(
		pika.ConnectionParameters(host='rmq'))
		channel2 = connection.channel()
		print(' [*] Waiting for messages in slave')   
		channel2.queue_declare(queue='readQ', durable=True)
		channel2.basic_consume(queue='readQ', on_message_callback=callbackread)
		channel2.start_consuming()
	t1 = threading.Thread(target=s) 
	t1.start()
	t2 = threading.Thread(target=r) 
	t2.start()


#MASTER
if(sys.argv[1]=='master'):
	print("In master")
	cont_id = os.popen("hostname").read().strip()
	path_master=cont_id+".db"
	temp_db="master.db"
	sql_create_users_table = "CREATE TABLE IF NOT EXISTS users (id integer PRIMARY KEY,name text NOT NULL,password text);"
	sql_create_rider_table = "CREATE TABLE IF NOT EXISTS rider (id integer PRIMARY KEY,  created_by text,timestamp text, source text,destination text);"
	sql_create_shared_table = "CREATE TABLE IF NOT EXISTS shared (id integer PRIMARY KEY,ride_id text,shared_by text);"
	with sqlite3.connect(path_master) as con:
		cur=con.cursor()
		cur.execute(sql_create_users_table)
		cur.execute(sql_create_rider_table)
		cur.execute(sql_create_shared_table)
		con.commit()
	with sqlite3.connect(temp_db) as con:
		cur=con.cursor()
		cur.execute(sql_create_users_table)
		cur.execute(sql_create_rider_table)
		cur.execute(sql_create_shared_table)
		con.commit()


	connection = pika.BlockingConnection(
	pika.ConnectionParameters(host='rmq'))
	channel = connection.channel()
	channel.queue_declare(queue='writeQ', durable=True)
	print(' [*] Waiting for messages in master')
	channel.basic_consume(queue='writeQ', on_message_callback=callbackwrite)
	channel.start_consuming()

