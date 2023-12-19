#!/bin/sh

# Run the MYSQL container with a database names users and credentials for a users-service which can access it
echo 'starting DB...'
sudo docker run --name userdb -d \
	-e MYSQL_ROOT_PASSWORD=1234 \
	-e MYSQL_DATABASE=users -e MYSQL_USER=root -e MYSQL_PASSWORD=1234 \
	-p 3306:3306 \
	mysql:latest

# Wait for database service to start up
echo "waiting for DB to start up..."
sudo docker exec userdb mysqladmin --silent --wait=30 -uroot -p1234 ping || exit

# Run the setup script
echo "Setting up the initial script..."
sudo docker exec userdb mysql -uroot -p1234 users < user.sql
