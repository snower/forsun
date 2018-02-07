forsun
======

高性能的定时调度服务。

About
=====

使用Linux系统定时器产生精确到秒的定时，长时间运行无误差，支持内存存储和redis持久化存储，轻松支持千万级定时任务调度，支持shell、http、reids、thrift、beanstalk五种到时触发回调方式，并可以通过扩展轻松自定义回调器。

使用crontab相似命令创建管理任务，同时Thrift接口创建和取消任务，支持大量语言接入。

Installation
============

::

    pip install forsun

    or 

    git clone https://github.com/snower/forsun.git
    python setup.py install

Start Server
============

::

    forsund -h
    usage: forsund [-h] [--bind BIND_HOST] [--port BIND_PORT] [--demon DEMON]
                   [--log LOG_FILE] [--log-level LOG_LEVEL] [--driver DRIVER]
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
      --demon DEMON         run demon mode
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

Command
=======

::

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

    #time模式（定点时间，每天16:32:00运行）
    forsun "set redis 0 32 16 * * * redis 'host=172.16.0.2;command=\'SET b 1 EX 300\'"
    forsun "set shell 0 32 16 * * * shell 'cmd=ls"
    forsun "set beanstalk 0 32 16 * * * beanstalk 'host=10.4.14.14;name=etask;body={}'"
    forsun "set thrift 0 32 16 * * * thrift 'host=10.4.14.14;port=4220"
    forsun "set http 0 32 16 * * * http 'url=\'http://www.baidu.com\''"

License
=======

forsun uses the MIT license, see LICENSE file for the details.
