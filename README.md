# forsun

高性能的定时调度服务。

# About

使用Linux系统定时器产生精确到秒的定时，长时间运行无误差，支持内存存储和redis持久化存储，轻松支持千万级定时任务调度，支持shell、http、reids、thrift、beanstalk、mysql六种到时触发回调方式，并可以通过扩展轻松自定义回调器。

使用crontab相似命令创建管理任务，同时Thrift接口创建和取消任务，支持大量语言接入。

# Installation

```
pip install forsun

or 

git clone https://github.com/snower/forsun.git
python setup.py install
```

# Start Server

```
usage: forsund [-h] [--bind BIND_HOST] [--port BIND_PORT] [--http HTTP_BIND]
               [--demon [DEMON]] [--log LOG_FILE] [--log-level LOG_LEVEL]
               [--driver DRIVER]
               [--driver-mem-store-file STORE_MEM_STORE_FILE]
               [--driver-redis-host DRIVER_REDIS_HOST]
               [--driver-redis-port DRIVER_REDIS_PORT]
               [--driver-redis-db DRIVER_REDIS_DB]
               [--driver-redis-prefix DRIVER_REDIS_PREFIX]
               [--driver-redis-server-id DRIVER_REDIS_SERVER_ID]
               [--extension-path EXTENSION_PATH] [--extension EXTENSIONS]

High-performance timing scheduling service

optional arguments:
  -h, --help            show this help message and exit
  --bind BIND_HOST      bind host (default: 0.0.0.0)
  --port BIND_PORT      bind port (default: 6458)
  --http HTTP_BIND      bind http server (default: ) example: 0.0.0.0:80
  --demon [DEMON]       run demon mode
  --log LOG_FILE        log file
  --log-level LOG_LEVEL
                        log level (defaul: INFO)
  --driver DRIVER       store driver mem or redis (defaul: mem)
  --driver-mem-store-file STORE_MEM_STORE_FILE
                        store mem driver store file (defaul:
                        /tmp/forsun.session)
  --driver-redis-host DRIVER_REDIS_HOST
                        store reids driver host (defaul: 127.0.0.1)
  --driver-redis-port DRIVER_REDIS_PORT
                        store reids driver port (defaul: 6379)
  --driver-redis-db DRIVER_REDIS_DB
                        store reids driver db (defaul: 0)
  --driver-redis-prefix DRIVER_REDIS_PREFIX
                        store reids driver key prefix (defaul: forsun)
  --driver-redis-server-id DRIVER_REDIS_SERVER_ID
                        store reids driver server id (defaul: 0)
  --extension-path EXTENSION_PATH
                        extension path
  --extension EXTENSIONS
                        extension name
```

### 使用内存持久化存储启动：

```
forsund --bind=0.0.0.0 --port=6458 --log=/var/log/forsun.log --log-level=INFO --driver=mem --driver-mem-store-file=/var/lib/fousun/forsun.session --demon
```

### 使用redis持久化存储启动：

```
forsund --bind=0.0.0.0 --port=6458 --log=/var/log/forsun.log --log-level=INFO --driver=redis --driver-redis-host=127.0.0.1 --driver-redis-db=1 --demon
```

### 提供http接口：

```
forsund --bind=0.0.0.0 --port=6458 --http=0.0.0.0:9001 --log=/var/log/forsun.log --log-level=INFO --driver=redis --driver-redis-host=127.0.0.1 --driver-redis-db=1 --demon
```

# Command

```
forsun -h
usage: forsun [-h] [--host HOST] [--port PORT] [--exe EXECUTE] [cmd]

High-performance timing scheduling service

positional arguments:
  cmd            execute cmd (default: )

optional arguments:
  -h, --help     show this help message and exit
  --host HOST    host (default: 127.0.0.1)
  --port PORT    port (default: 6458)
  --exe EXECUTE  execute cmd (default: )
  
#timeout模式（每5秒运行，共运行1次）
forsun "set redis */5/1 * * * * * redis 'host=172.16.0.2;command=\'SET b 1 EX 300\'"
forsun "set shell */5/1 * * * * * shell 'cmd=ls"
forsun "set beanstalk */5/1 * * * * * beanstalk 'host=10.4.14.14;name=etask;body={}'"
forsun "set thrift */5/1 * * * * * thrift 'host=10.4.14.14;port=4220"
forsun "set http */5/1 * * * * * http 'url=\'http://www.baidu.com\''"
forsun "set mysql */5/1 * * * * * mysql 'host=172.16.0.2;user=root;passwd=123456;db=test;sql=\'update test set created_at=now() where id=1\'"

#time模式（定点时间，每天16:32:00运行）
forsun "set redis 0 32 16 * * * redis 'host=172.16.0.2;command=\'SET b 1 EX 300\'"
forsun "set shell 0 32 16 * * * shell 'cmd=ls"
forsun "set beanstalk 0 32 16 * * * beanstalk 'host=10.4.14.14;name=etask;body={}'"
forsun "set thrift 0 32 16 * * * thrift 'host=10.4.14.14;port=4220"
forsun "set http 0 32 16 * * * http 'url=\'http://www.baidu.com\''"
forsun "set mysql 32 16 * * * mysql 'host=172.16.0.2;user=root;passwd=123456;db=test;sql=\'update test set created_at=now() where id=1\'"
```

# Thrift Interface

```
exception ForsunPlanError{
    1:i16 code,
    2:string message
}

struct ForsunPlan {
    1: required bool is_time_out,
    2: required string key,
    3: required i16 second,
    4: i16 minute = -1,
    5: i16 hour = -1,
    6: i16 day = -1,
    7: i16 month = -1,
    8: i16 week = -1,
    9: required i32 next_time,
    10: i16 status = 0,
    11: i16 count = 0,
    12: i16 current_count = 0,
    13: i32 last_timeout = 0,
    14:string action = "shell",
    15:map<string, string> params = {}
}

service Forsun{
    i16 ping(),
    ForsunPlan create(1:string key, 2:i16 second, 3:i16 minute = -1, 4:i16 hour = -1, 5:i16 day = -1, 6:i16 month = -1, 7:i16 week = -1, 8:string action="shell", 9:map<string, string> params={}) throws (1:ForsunPlanError err),
    ForsunPlan createTimeout(1:string key, 2:i16 second, 3:i16 minute = -1, 4:i16 hour = -1, 5:i16 day = -1, 6:i16 month = -1, 7:i16 week = -1, 8:i16 count=1, 9:string action="shell", 10:map<string, string> params={}) throws (1:ForsunPlanError err),
    ForsunPlan remove(1:string key) throws (1:ForsunPlanError err),
    ForsunPlan get(1:string key) throws (1:ForsunPlanError err),
    list<ForsunPlan> getCurrent(),
    list<ForsunPlan> getTime(1:i32 timestamp),
    list<string> getKeys(1:string prefix),
    void forsun_call(1:string key, 2:i32 ts, 3:map<string, string> params)
}
```

# Docker

使用docker运行，注意：使用docker运行时，shell和宿主机在同一环境，执行shell时将在docker中运行。

```
git clone https://github.com/snower/forsun
cd forsun

#创建保存redis持久化数据文件夹和日志文件夹，可自定义
mkdir /var/lib/forsun
mkdir /var/log/forsun

#build
docker build -t forsun:0.0.4 .
#start
docker run -d -p 6458:6458 -p 9002:9002 -v /var/lib/forsun:/var/lib/forsun -v /var/log/forsun:/var/log/forsun forsun:0.0.4
```

# Action

回调器参数为create和createTimeout最后一个参数params key和value的map。

## shell参数

* cmd shell命令
* cwd 工作目录
* env 环境变量，以;分割＝号连接的字符串，如：a=1;b=c

## http参数

* url 请求接口URL字符串
* method 请求方法，只支持get,post,put,delete,head五种方法
* body 请求体字符串
* header_ 以header_为前缀的key都会放到请求header中
* auth_username 校验用户名
* auth_password 校验密码
* auth_mode 校验方法
* user_agent 请求User－Agent
* connect_timeout 连接超时时间，默认5秒
* request_timeout 请求超时时间，默认60秒

## redis参数

* host redis服务器地址，默认127.0.0.1
* port redis服务器端口，默认6379
* selected_db redis运行命令db
* max_connections 连接redis服务器最大连接数，第一次连接时的命令中的值有效
* command 需要执行的命令，多条命令以;分割

## mysql参数

* host mysql服务器地址，默认127.0.0.1
* port mysql服务器端口，默认3306
* db mysql运行命令db，默认mysql
* user mysql登陆用户名，默认root
* passwd mysql登陆密码，默认空字符串
* max_connections 连接redis服务器最大连接数，第一次连接时的命令中的值有效
* sql 需要执行的sql

## beanstalk参数

* host beanstalk服务器地址，默认127.0.0.1
* port beanstalk服务器端口，默认11300
* name 队列名称，默认default
* body 推送的消息体

## thrift参数

回调thrift接口时，固定请求void forsun_call(1:string key, 2:i32 ts, 3:map<string, string> params)该函数，第三个params参数即为任务定义时的params值。

* host thrift服务器地址，默认127.0.0.1
* port thrift服务器端口，默认5643
* max_connections 连接thrift服务器最大连接数，第一次连接时的命令中的值有效


# License

forsun uses the MIT license, see LICENSE file for the details.