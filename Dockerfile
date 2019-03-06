FROM ubuntu:16.04

MAINTAINER snower  sujian199@gmail.com

VOLUME ['/var/lib/forsun', '/var/log/forsun']

EXPOSE 6458
EXPOSE 9002

WORKDIR /var/lib/forsun

RUN apt-get update \
    && apt-get install -y python3 \
    && apt-get install -y python3-pip \
    && apt-get install -y redis-server \
    && pip3 install tornado==5.1 \
    && pip3 install thrift==0.11.0 \
    && pip3 install torthrift==0.2.4 \
    && pip3 install tornadis==0.8.1 \
    && pip3 install msgpack==0.5.1 \
    && pip3 install forsun==0.1.0 \
    && pip3 install beanstalkt==0.7.0 \
    && pip3 install pymysql==0.7.10 \
    && pip3 install tormysql==0.3.7 \
    && sed -i 's/logfile \/var\/log\/redis\/redis-server.log/logfile \/var\/log\/forsun\/redis\/redis-server.log/g' /etc/redis/redis.conf \
    && sed -i 's/dir \/var\/lib\/redis/dir \/var\/lib\/forsun\/redis/g' /etc/redis/redis.conf \
    && sed -i 's/# maxclients 10000/maxclients 1024/g' /etc/redis/redis.conf

COPY docker/start.sh /root/

CMD /root/start.sh