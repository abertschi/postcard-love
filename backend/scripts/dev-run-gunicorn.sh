#!/usr/bin/env bash

cd ..
gunicorn --bind 0.0.0.0:5080 wsgi:app
