#!/bin/bash
sudo apt-get update
sudo apt-get install -y build-essential docker.io docker-compose
sudo systemctl start docker
sudo systemctl enable docker
git clone https://github.com/pablobuenaposada/LockMyTag.git /opt/LockMyTag
cd /opt/LockMyTag
make docker/up
make docker/create-super-user