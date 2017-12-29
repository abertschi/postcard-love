#!/usr/bin/env bash

gunicorn --bind 0.0.0.0:5080 wsgi:app
