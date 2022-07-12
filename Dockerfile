FROM ubuntu:20.04

MAINTAINER snower sujian199@gmail.com

VOLUME /forsun

EXPOSE 6458
EXPOSE 9002

WORKDIR /forsun

COPY docker/startup.sh /opt/

RUN apt-get update \
    && apt-get install -y python \
    && apt-get install -y python-pip \
    && pip install tornado==5.1 \
    && pip install thrift==0.11.0 \
    && pip install torthrift==0.2.4 \
    && pip install tornadis==0.8.1 \
    && pip install msgpack==0.5.1 \
    && pip install forsun==0.1.4 \
    && pip install beanstalkt==0.7.0 \
    && pip install pymysql==0.7.10 \
    && pip install tormysql==0.3.7 \
    && chmod +x /opt/startup.sh

CMD /opt/startup.sh