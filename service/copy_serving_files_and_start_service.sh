#!/bin/bash

sudo apt update -y
sudo apt install -y build-essential libssl-dev libffi-dev nginx python3-certbot-nginx
sudo ufw disable

# Before running this script, the moalmanac account must own a conda install at /srv/moalmanac/miniforge3 with this
# repository's environment built in it. See service/README.md.

# The API listens on 127.0.0.1:8000, where it is used by nginx and by moalmanac-browser instances on the same VM
sudo cp moalmanac-api.service /etc/systemd/system/moalmanac-api.service
sudo systemctl daemon-reload
sudo systemctl enable --now moalmanac-api

sudo cp moalmanac-api /etc/nginx/sites-available/moalmanac-api
sudo ln -sf /etc/nginx/sites-available/moalmanac-api /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl restart nginx

sudo chmod 755 /srv/moalmanac
