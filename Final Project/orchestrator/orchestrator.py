#!/usr/bin/env python
import json 
import pika
import sys
import uuid
import os
import logging
from flask import Flask, request, jsonify, make_response
from flask import render_template, redirect, url_for, abort
import datetime
from functools import wraps
from kazoo.client import KazooClient
from kazoo.client import KazooState
import requests
import json
import subprocess
import docker
import threading
import time
import math
import re
import flask
app = Flask(__name__)
headers={"Content-Type":"application/json"}
first_time_slave=True
first_time_master=True
master=0

dic1 ={"slave" :0,"master" :0} 
with open("count1.json", "w") as outfile1: 
    json.dump(dic1, outfile1) 
#count of read requests
dic ={"count" :0} 
with open("count.json", "w") as outfile: 
    json.dump(dic, outfile) 

#list of slave and master apis
master_slave ={"slave" :[],"master":0} 

orchestrator_id = os.popen("hostname").read().strip()

logging.basicConfig()

class Read(object):

    def __init__(self):
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(host='rmq'))

        self.channel = self.connection.channel()

        request= self.channel.queue_declare(queue='readQ',durable = True)
        self.read_queue = request.method.queue

        result = self.channel.queue_declare(queue='responseQ', durable = True)
        self.callback_queue = result.method.queue

        self.channel.basic_consume(
            queue=self.callback_queue,
            on_message_callback=self.on_response,
            auto_ack=True)
        

    def on_response(self, ch, method, props, body):
        if self.corr_id == props.correlation_id:
            self.response = body

    def call(self, n):
        self.response = None
        self.corr_id = str(uuid.uuid4())
        self.channel.basic_publish(
            exchange='',
            routing_key=self.read_queue,
            properties=pika.BasicProperties(
                reply_to=self.callback_queue,
                correlation_id=self.corr_id,
            ),
            body=json.dumps(n))
        while self.response is None:
            self.connection.process_data_events()

        self.connection.close()
        print(self.response)
        return self.response

class Write(object):

    def __init__(self):
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(host='rmq'))

        self.channel = self.connection.channel()

        request= self.channel.queue_declare(queue='writeQ',durable = True)
        self.read_queue = request.method.queue

        result = self.channel.queue_declare(queue='writeResponseQ', durable = True)
        self.callback_queue = result.method.queue

        self.channel.basic_consume(
            queue=self.callback_queue,
            on_message_callback=self.on_response,
            auto_ack=True)
        

    def on_response(self, ch, method, props, body):
        if self.corr_id == props.correlation_id:
            self.response = body 

    def call(self, n):
        self.response = None
        self.corr_id = str(uuid.uuid4())
        self.channel.basic_publish(
            exchange='',
            routing_key=self.read_queue,
            properties=pika.BasicProperties(

                reply_to=self.callback_queue,
                correlation_id=self.corr_id,
            ),
            body=json.dumps(n))
        while self.response is None:
            self.connection.process_data_events()

        self.connection.close()
        print(self.response)
        return self.response

class update_slave(object):

    def __init__(self):
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(host='rmq'))

        self.channel = self.connection.channel()

        request= self.channel.queue_declare(queue='update_slaveQ',durable = True)
        self.read_queue = request.method.queue

        result = self.channel.queue_declare(queue='write_slaveQ', durable = True)
        self.callback_queue = result.method.queue

        self.channel.basic_consume(
            queue=self.callback_queue,
            on_message_callback=self.on_response,
            auto_ack=True)
        

    def on_response(self, ch, method, props, body):
        if self.corr_id == props.correlation_id:
            self.response = body 

    def call(self, n):
        self.response = None
        self.corr_id = str(uuid.uuid4())
        self.channel.basic_publish(
            exchange='',
            routing_key=self.read_queue,
            properties=pika.BasicProperties(
                reply_to=self.callback_queue,
                correlation_id=self.corr_id,
            ),
            body=json.dumps(n))
        while self.response is None:
            self.connection.process_data_events()

        self.connection.close()
        print(self.response)
        return self.response

def create_slave():
	global master_slave
	client = docker.from_env()
	client.images.build(path=".", tag="slave")
	client.containers.create("slave",detach=True)
	id=client.containers.run("slave",command="python worker.py slave",network='orchestrator_default',links={'rmq':'rmq'},detach=True,volumes_from=[orchestrator_id])
	pid=id.top()['Processes'][0][1]
	if zk.exists("/orchestrator/"+str(pid)):
	    print("Node already exists")
	else:
	    zk.create("/orchestrator/"+str(pid), b"0")
	master_slave["slave"].append(int(pid))
	updateObj = update_slave()


def reduce_slaves():
	global master_slave
	client = docker.from_env()
	temp=client.containers.list() 
	print("container list", temp) 
	container_name=client.containers.get(str(temp[0].id)) 
	print("slave is going to get deleted", container_name)
	pid=container_name.top()['Processes'][0][1]
	print("slave is going to get deleted of pid : ",pid)
	master_slave["slave"].remove(int(pid))
	container_name.kill()

def update_func():
	global master_slave
	global master
	print('in Scale checking')
	client = docker.from_env()
	with open("count.json", "r") as jsonFile:
	    data = json.load(jsonFile)
	with open("count1.json", "r") as jsonFile1:
	    data1 = json.load(jsonFile1)
	print("Count of requests: ",data["count"])
	if(data["count"]==0):
		total_slaves=1
	else:
		total_slaves=math.ceil(data["count"]/20) 
	print("needed slaves: ",total_slaves)
	list_pid = master_slave["slave"]
	current_slaves=len(list_pid)
	n=current_slaves
	if n>total_slaves:
		print("No.of slaves removed:",abs(int(total_slaves-current_slaves)))
	if n<total_slaves:
		print("No.of slaves added:",int(total_slaves-current_slaves))
	while(total_slaves!=n):
		if(n>total_slaves):
			print("reduceing ")
			reduce_slaves()
			n=n-1
		else:
			create_slave()
			n=n+1
	with open("count.json", "r") as jsonFile:
	    data = json.load(jsonFile)
	data["count"] = 0
	data1["slave"] = total_slaves
	with open("count.json", "w") as jsonFile:
	    json.dump(data, jsonFile)
	with open("count1.json", "w") as jsonFile1:
	    json.dump(data1, jsonFile1)
	timer = threading.Timer(120.0,update_func) 
	timer.start() 
	
'''

#AP1:1	
@app.route('/api/v1/users', methods=['PUT'])
def create_user():
	data = request.get_json(force=True)
	pattern = re.compile(r'\b[0-9a-f]{40}\b')
	if(bool(pattern.match(data['password']))!=True):
		abort(400)
	req=requests.post(request.url_root+"/api/v1/db/write",headers=headers, json={"api":"1","name":data['username'],"password":data['password']})
	if(req.json()=="True"):
		status_code = flask.Response(status=201)
		return status_code
	else:
		abort(400)
#AP1:2
@app.route('/api/v1/users/<string:username>', methods=['DELETE'])
def remove_user(username):
	req=requests.post(request.url_root+"/api/v1/db/write", json ={"api":"2","name":username})
	if(req.json()=="True"):
		status_code = flask.Response(status=201)
		return status_code
	else:
		abort(400)

#AP1:3
@app.route('/api/v1/rides', methods=['POST'])
def create_rider():
	data = request.get_json(force=True)
	req=requests.post(request.url_root + "/api/v1/db/write", json ={"api":"3","created_by":data['created_by'], "timestamp":data['timestamp'], "source":data['source'], "destination":data['destination']},headers=headers)
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
	read_data1 = requests.post(request.url_root+"/api/v1/db/read",json={"api":"4"})
	read_data1 = read_data1.json()
	read_data={}
	s=[i.split(",") for i in read_data1.split(";")]
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
	if request.method == 'GET':
		r=requests.post(request.url_root+"/api/v1/db/read", json ={"api":"5","ride_id":str(ride_id)},headers=headers)
		r=r.json()
		s=r.split(";")
		s[0]=s[0][1:]
		if(s[2]=='Empty'):
			s[2]=[]
		else:
			s[2]=s[2].split(":")
		s[0]=int(s[0])
		s[4]=int(s[4])
		s[5]=int(s[5])
		ride_data={}
		ride_data['rideId']=s[0]
		ride_data['created_by']=s[1]
		ride_data['users']=s[2]
		ride_data['timestamp']=s[3]
		ride_data['source']=s[4]
		ride_data['destination']=s[5]
		return jsonify(ride_data)	
	elif request.method == 'POST':
		req=requests.post(request.url_root+"/api/v1/db/write", json ={"api":"6","ride_id":str(ride_id),"shared_by":request.get_json(force=True)['username']})
		if(req.json()=="True"):
			status_code = flask.Response(status=200)
			return status_code
		else:
			status_code = flask.Response(status=204)
			return status_code

	elif request.method == 'DELETE':
		req=requests.post(request.url_root+"/api/v1/db/write", json ={"api":"7","ride_id":str(ride_id)})
		if(req.json()=="True"):
			status_code = flask.Response(status=200)
			return status_code
		else:
			abort(400)
'''

#API10
@app.route('/api/v1/db/clear',methods=['POST'])
def clear_db():
	req=requests.post(request.url_root+"/api/v1/db/write", json ={"api":"11"})
	if(req.json()=="True"):
		status_code = flask.Response(status=200)
		return status_code
	else:
		abort(400)


@app.route('/api/v1/worker/list1',methods=['POST'])
def list_workers():
	if(request.method!="POST"):
		abort(405)
	l=[]
	l=master_slave["slave"]
	with open("count.json", "r") as jsonFile:
	    data = json.load(jsonFile)
	#print("Count of requests: ",data["count"])
	if(data["count"]==0):
		total_slaves=1
	else:
		total_slaves=math.ceil(data["count"]/20) 
	#print("total slaves: ",total_slaves)
	#l.append(master_slave["master"])
	return {"slave":l,"master":int(master_slave["master"])}

@app.route('/api/v1/worker/list',methods=['GET'])
def list_workers1():
	if(request.method!="POST"):
		abort(405)
	children = zk.get_children("/orchestrator", watch=demo_func)
	print("There are %s children with names %s" % (len(children), children))
	children=[int(i) for i in children]
	return jsonify(children)

@app.route('/api/v1/db/read', methods=['POST'])
def read_db():
	if(request.method!="POST"):
		abort(405)
	global first_time_slave
	global master_slave
	if(first_time_slave==True):
		client = docker.from_env()
		client.images.build(path=".", tag="slave")
		client.containers.create("slave",detach=True)
		id=client.containers.run("slave",command="python worker.py slave",network='orchestrator_default',links={'rmq':'rmq'},detach=True,volumes_from=[orchestrator_id])
		pid=id.top()['Processes'][0][1]
		if zk.exists("/orchestrator/"+str(pid)):
		    print("Node already exists")
		else:
		    zk.create("/orchestrator/"+str(pid), b"0")
		master_slave["slave"].append(int(pid))
		with open("count1.json", "r") as jsonFile1:
	    		data1 = json.load(jsonFile1)
		data1["slave"]=1
		with open("count1.json", "w") as jsonFile1:
	    		json.dump(data1, jsonFile1)
		first_time_slave=False
		timer = threading.Timer(120.0,update_func) 
		timer.start() 
	with open("count.json", "r") as jsonFile:
	    data = json.load(jsonFile)
	tmp = data["count"]
	data["count"] =tmp+1
	with open("count.json", "w") as jsonFile:
	    json.dump(data, jsonFile)
	resObj = Read()
	response = resObj.call(request.get_json(force=True))
	res=response.decode()
	print(" [.] Got Response for READ:%r" % res)
	return jsonify(res)
	del(respObj)

@app.route('/api/v1/db/write', methods=['POST'])
def write_db():
	if(request.method!="POST"):
		abort(405)
	global first_time_master
	global master_slave
	if(first_time_master==True):
		client = docker.from_env()
		client.images.build(path=".", tag="master")
		client.containers.create("master",detach=True)
		id=client.containers.run("master",command="python worker.py master",network='orchestrator_default',links={'rmq':'rmq'},detach=True,volumes_from=[orchestrator_id])
		pid=id.top()['Processes'][0][1]
		if zk.exists("/orchestrator/"+str(pid)):
		    print("Node already exists")
		else:
		    zk.create("/orchestrator/"+str(pid), b"1")
		master_slave['master']=pid
		with open("count1.json", "r") as jsonFile1:
	    		data1 = json.load(jsonFile1)
		data1["master"]=1
		with open("count1.json", "w") as jsonFile1:
	    		json.dump(data1, jsonFile1)
		print("pid of master: ",master_slave['master'])
		first_time_master=False
		master=id
	print("In write API")
	writeObj = Write()
	Wresponse = writeObj.call(request.get_json(force=True)).decode()
	print(" [.] Got Response for WRITE:%r" % Wresponse)
	#print (json.loads(Wresponse))
	return jsonify(Wresponse)
	del(writeObj)

################-ZooKeeper-##################
zk = KazooClient(hosts='zoo:2181')
zk.start()
zk.delete("/orchestrator", recursive=True)

# Ensure a path, create if necessary
zk.ensure_path("/orchestrator")

@zk.ChildrenWatch('/orchestrator')
def demo_func(child):
	print('in Zookeeper')
	global slave_num
	print(child)
	slave_list=[]
	with open("count1.json", "r") as jsonFile1:
	    data1 = json.load(jsonFile1)
	slave = data1["slave"]
	for i in child:
		data,stat=zk.get('/orchestrator/'+str(i).strip())
		if(data.decode('utf-8')=='0'):
			slave_list.append(i)
	print("slave_list:"+str(slave_list))
	print('slave:',str(slave), 'slaves:',str(len(slave_list)))
	slaves=len(slave_list)
	result = slaves-slave
	print("result inside watch",result)
	if(result==0):
		print("All slaves are working properly ")
	if(result<0):
		for i in range(abs(result)):
			create_slave()
			time.sleep(2)


@app.route('/api/v1/crash/slave',methods=['POST'])
def crash_slave():
	if(request.method!="POST"):
		abort(405)
	print('in crash slave')
	client = docker.from_env()
	top_pid = master_slave['slave'][-1]
	data, stat = zk.get("/orchestrator/"+str(top_pid).strip())
	print("Version: %s, data: %s" % (stat.version, data.decode("utf-8")))
	s = data.decode("utf-8")
	if (s=="0"):
		x="docker ps -q | xargs docker inspect --format '{{.State.Pid}}, {{.Id}}' | grep "+str(top_pid).strip()
		proc = subprocess.Popen([x], stdout=subprocess.PIPE, shell=True)
		(out, err) = proc.communicate()
		out=out.decode("utf-8")
		l=out.split(",")
		print("container_id",str(l[1]))
		cid=str(l[1]).strip()
		container_name=client.containers.get(str(cid))
		print("slave is going to get deleted ",container_name)
		container_name.kill()
		container_name.remove()
		zk.delete("/orchestrator/"+ str(top_pid).strip())
		master_slave['slave'] = master_slave['slave'][:-1]
		global flag
		flag=1
		time.sleep(1)
		flag=0
		l=[]
		l.append(top_pid)
		return jsonify(l),200

if __name__ == '__main__':
	app.run(host='0.0.0.0',port=80,debug=True)

