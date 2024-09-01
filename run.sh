#!bin/bash

sleep 10
python3 manage.py migrate --settings=mailcollector.settings
gunicorn mailcollector.wsgi:application --bind 0.0.0.0:3002