#!/bin/bash

sudo apt install python3-certbot-nginx
sudo certbot --nginx -d api.moalmanac.org -d www.api.moalmanac.org