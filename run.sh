#!/usr/bin/env bash

export FLASK_APP=monolith
export FLASK_ENV=development
export FLASK_DEBUG=true
flask run
#celery -A monolith.background worker -l debug &
#celery -A monolith.background beat -l debug &
