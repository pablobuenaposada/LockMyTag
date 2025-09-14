#!/bin/bash
sudo apt-get update

# enable swap
sudo fallocate -l 1G /swapfile && \
sudo chmod 600 /swapfile && \
sudo mkswap /swapfile && \
sudo swapon /swapfile && \
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

# install docker compose
sudo apt-get install curl
mkdir -p ~/.docker/cli-plugins/
curl -SL https://github.com/docker/compose/releases/download/v2.39.2/docker-compose-linux-x86_64 -o ~/.docker/cli-plugins/docker-compose
chmod +x ~/.docker/cli-plugins/docker-compose

# install docker
sudo apt-get install -y build-essential docker.io
sudo systemctl start docker
sudo systemctl enable docker

# install the project
git clone https://github.com/pablobuenaposada/LockMyTag.git /opt/LockMyTag
cd /opt/LockMyTag
make docker/up-prod