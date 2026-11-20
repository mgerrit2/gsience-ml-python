# GScience ML webservice
## Purpose
Test project, to implement ml in python as webservice

# API doc
http://127.0.0.1:8000/docs

# Render servivce
## Basis url
https://gsience-ml-python.onrender.com/


## Add prometheus

pip install fastapi uvicorn prometheus-fastapi-instrumentator

[prometeus metrics](http://172.22.128.1:8000/metrics)

[prometeus ui](http://172.22.128.1:9090)


## Connection in grafana
Connection string:
http://prometheus:9090

url:http://localhost:3000/