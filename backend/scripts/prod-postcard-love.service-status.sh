#!/usr/bin/env bash

RED="\e[31m"
RES="\e[0m"
echo -e "${RED}status gunicorn postcard-love ${RES}"
sudo systemctl status postcard-love.service -l


