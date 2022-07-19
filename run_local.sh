#!/bin/bash

SERVER_PORT=${1-5000}
export SERVER_PORT=${SERVER_PORT}
export DATABASE_HOST=localhost
export DATABASE_PORT=5432
export DATABASE_USER=dhos-fuego-api
export DATABASE_PASSWORD=dhos-fuego-api
export DATABASE_NAME=dhos-fuego-api
export AUTH0_DOMAIN=https://login-sandbox.sensynehealth.com/
export AUTH0_AUDIENCE=https://dev.sensynehealth.com/
export ENVIRONMENT=DEVELOPMENT
export ALLOW_DROP_DATA=true
export PROXY_URL=http://localhost
export HS_KEY=secret
export FLASK_APP=dhos_fuego_api/autoapp.py
export IGNORE_JWT_VALIDATION=true
export REDIS_INSTALLED=False
export LOG_FORMAT=colour
export FHIR_SERVER_AUTH_METHOD=basic
export FHIR_SERVER_BASE_URL=http://localhost:80/fhir
export FHIR_SERVER_TOKEN_URL=None
export FHIR_SERVER_CLIENT_ID=SensyneHealth
export FHIR_SERVER_CLIENT_SECRET=UnbelievablyComplexPassword123qwerty
export FHIR_SERVER_MRN_SYSTEM=https://commure.com/fhir/identifiers/Patient/MRN

set -ex

if [ -z "$*" ]
then
   flask db upgrade
   docker-compose -f hapi.docker-compose.yaml up -d
   python -m dhos_fuego_api
   docker-compose -f hapi.docker-compose.yaml down
else
flask $*
fi
