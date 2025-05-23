#!/bin/bash

sudo apt update -y
sudo apt install -y build-essential libssl-dev libffi-dev nginx python3-certbot-nginx
sudo ufw disable

#sudo wget https://github.com/conda-forge/miniforge/releases/download/24.7.1-0/Mambaforge-pypy3-24.7.1-0-Linux-x86_64.sh
#bash Mambaforge-pypy3-24.7.1-0-Linux-x86_64.sh
# restart shell (close out of VM and open a new one)
# conda create virtual env, make sure that conda is installed correctly
# activate venv and install requirements into it

sudo cp moalmanac-api.service /etc/systemd/system/moalmanac-api.service
sudo systemctl start moalmanac-api
sudo systemctl enable moalmanac-api

sudo cp moalmanac-api /etc/nginx/sites-available/
sudo ln -s /etc/nginx/sites-available/moalmanac-api /etc/nginx/sites-enabled
sudo systemctl restart nginx

sudo chmod 755 /home/breardon
