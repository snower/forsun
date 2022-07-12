#!/bin/bash

if [ ! -d "/forsun" ]; then
  mkdir /forsun
fi

if [ ! -d "/forsun/data" ]; then
  mkdir /forsun/data
fi

cd /forsun || exit

CMD_ARG="--bind=\"0.0.0.0\" --http=\"0.0.0.0:9002\" --port=6458 --nodemon"

if [ -n "$ARG_LOG" ]; then
  CMD_ARG="$CMD_ARG --log=\"$ARG_LOG\""
else
  CMD_ARG="$CMD_ARG --log=-"
fi

if [ -n "$ARG_LOG_LEVEL" ]; then
  CMD_ARG="$CMD_ARG --log_level=\"$ARG_LOG_LEVEL\""
fi

DRIVER="mem"
if [ -n "$ARG_DRIVER" ]; then
  DRIVER="$ARG_DRIVER"
fi

if [ "$DRIVER" == "mem" ]; then
  CMD_ARG="$CMD_ARG --driver=mem"
  if [ -n "$ARG_STORE_MEM_STORE_FILE" ]; then
    CMD_ARG="$CMD_ARG --driver-mem-store-file=$ARG_STORE_MEM_STORE_FILE"
  else
    CMD_ARG="$CMD_ARG --driver-mem-store-file=/forsun/data"
  fi
else
  CMD_ARG="$CMD_ARG --driver=redis"
  if [ -n "$ARG_DRIVER_REDIS_HOST" ]; then
    CMD_ARG="$CMD_ARG --driver-redis-host=$ARG_DRIVER_REDIS_HOST"
  fi

  if [ -n "$ARG_DRIVER_REDIS_PORT" ]; then
    CMD_ARG="$CMD_ARG --driver-redis-port=$ARG_DRIVER_REDIS_PORT"
  fi

  if [ -n "$ARG_DRIVER_REDIS_PASSWORD" ]; then
    CMD_ARG="$CMD_ARG --driver-redis-password=\"$ARG_DRIVER_REDIS_PASSWORD\""
  fi

  if [ -n "$ARG_DRIVER_REDIS_DB" ]; then
    CMD_ARG="$CMD_ARG --driver-redis-db=$ARG_DRIVER_REDIS_DB"
  fi

  if [ -n "$ARG_DRIVER_REDIS_PREFIX" ]; then
    CMD_ARG="$CMD_ARG --driver-redis-prefix=$ARG_DRIVER_REDIS_PREFIX"
  fi

  if [ -n "$ARG_DRIVER_REDIS_SERVER_ID" ]; then
    CMD_ARG="$CMD_ARG --driver-redis-server-id=$ARG_DRIVER_REDIS_SERVER_ID"
  fi
fi

if [ -n "$ARG_EXTENSION_PATH" ]; then
  CMD_ARG="$CMD_ARG --extension-path=$ARG_EXTENSION_PATH"
fi

if [ -n "$ARG_EXTENSIONS" ]; then
  CMD_ARG="$CMD_ARG --extension=$ARG_EXTENSIONS"
fi

if [ -n "$ARG_CONF" ]; then
  CMD_ARG="$CMD_ARG --conf=$ARG_CONF"
fi

CMD="forsund $CMD_ARG"
echo "$CMD"
exec $CMD