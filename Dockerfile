FROM python:2.7.14-stretch

RUN apt-get update
RUN apt-get install -y fuse

RUN mkdir -p /app/dirlist
WORKDIR /app/dirlist

RUN pip install fusepy && \
    pip install python-dateutil

RUN mkdir mount
