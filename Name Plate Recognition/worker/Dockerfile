FROM ubuntu

WORKDIR /srv
COPY worker.py /srv
COPY model-final /srv
RUN apt-get -y update
RUN apt install -y python
RUN apt-get install -y python-pip
RUN pip install pika redis
RUN pip --no-cache-dir install pandas
RUN pip install requests
RUN pip --no-cache-dir install sklearn
RUN cd /srv
CMD ["python", "worker.py"]
