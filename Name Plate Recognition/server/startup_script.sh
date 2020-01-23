#!/bin/bash

apt-get update
apt-get install -y python3 python3-pip git
pip3 install --upgrade google-api-python-client

mkdir flask
git clone https://github.com/pallets/flask.git flask
cd flask/examples/tutorial
python3 setup.py install
pip3 install -e .

pip3 install numpy
pip3 install pillow jsonpickle
pip3 install pika
pip3 install redis

cd /Lab8
python3 server.py
