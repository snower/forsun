#!/bin/bash

mkdir /var/lib/forsun/redis
chown -R redis:redis /var/lib/forsun/redis
mkdir /var/log/forsun/redis
chown -R redis:redis /var/log/forsun/redis
/etc/init.d/redis-server start
redis-cli get a || sleep 2 && redis-cli get a || exit
cd /var/lib/forsun
forsund --bind=0.0.0.0 --http=0.0.0.0:9002 --log=/var/log/forsun/forsun.log --log-level=INFO --driver=redis --driver-redis-host=127.0.0.1 --nodemon