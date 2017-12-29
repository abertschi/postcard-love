#!/usr/bin/env bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source $DIR/../../venv/bin/activate

cd ..
gunicorn --bind 0.0.0.0:5080 wsgi:app




