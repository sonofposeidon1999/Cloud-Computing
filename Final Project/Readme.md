## Introduction
Ride Share is an application built using REST flask APIs and deployed on Amazon’s AWS EC2 instance with the help of containers. It has various functionalities components such as creating a new user, creating a new ride, merging rides with users, deleting users. DThe whole database requests areis handled by an orchestrator, which employs aemployshas a master node to write into the database and slave node(s)(s) to read from the database. The orchestrator supports various features such as data consistency, scaling up, fault tolerance.

## Setup
#### 1. Prerequisites
  Make sure you have docker and docker-compose installed in your terminal.
  
#### 2. Download the files.
  Download the files or clone the repository onto your device.

#### 3. Create instances
  You are required to create instances for Rides, User and Orchestrator. Set up elastic IPs for each.

#### 4. Upload files
  Upload the respective folders in each of the instances.
  
#### 5. Set Orch_IP
  In the python code for User and Rides, at the beginning of the code, we have initialised a variable called ip_addr_orch. This must be set to the elastic ip address of the orchestrator.

#### 6. Create a load balancer
  Create a path-based load balancer with the following rules:
    a. If path is "api/v1/users", forward to User instance
    b. If path is anything else, forward to Rides instance

#### 7. Run the Orchestrator
  Delete any file with the extension .db and .json in the orchestrator folder. The program will create new ones at each initialization. Open the terminal and run the command "sudo docker-compose build" and then "sudo docker-compose up". The orchestrator would take a few minutes to install the required images and set up.

#### 8. Run the Rides and User
  Initialise and run the User and Ride instances. They will call the orchestrator instance by themselves to access database information as required.
  
#### 9. Test your application
  Using Postman or any other similar platform, use the DNS address of the Load Balancer to access the different APIs created in the project. Have fun!
  
## Acknowledgements
This project was created by 
- Malavikka R
- Daksha Singhal
- M Adithya Vardhan
