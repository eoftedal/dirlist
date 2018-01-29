FROM python:2.7.14-stretch

RUN apt-get update
RUN apt-get install -y fuse

RUN pip install fusepy && \
    pip install python-dateutil

RUN mkdir -p /app/dirlist
WORKDIR /app/dirlist

COPY dirlist.py /app/dirlist

RUN mkdir mount
