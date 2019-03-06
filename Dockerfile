FROM ubuntu:16.04

MAINTAINER snower  sujian199@gmail.com

VOLUME ['/var/lib/forsun', '/var/log/forsun']

EXPOSE 6458
EXPOSE 9002

WORKDIR /var/lib/forsun

RUN apt-get update \
    && apt-get install -y python \
    && apt-get install -y python-pip \
    && apt-get install -y redis-server \
    && pip install tornado==5.1 \
    && pip install thrift==0.11.0 \
    && pip install torthrift==0.2.4 \
    && pip install tornadis==0.8.1 \
    && pip install msgpack==0.5.1 \
    && pip install forsun==0.1.0 \
    && pip install beanstalkt==0.7.0 \
    && pip install pymysql==0.7.10 \
    && pip install tormysql==0.3.7 \
    && sed -i 's/logfile \/var\/log\/redis\/redis-server.log/logfile \/var\/log\/forsun\/redis\/redis-server.log/g' /etc/redis/redis.conf \
    && sed -i 's/dir \/var\/lib\/redis/dir \/var\/lib\/forsun\/redis/g' /etc/redis/redis.conf \
    && sed -i 's/# maxclients 10000/maxclients 1024/g' /etc/redis/redis.conf

COPY docker/start.sh /root/

CMD /root/start.sh