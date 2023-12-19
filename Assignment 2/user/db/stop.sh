#!/bin/sh

#stop the database and remove the container
sudo docker stop userdb && sudo docker rm userdb
