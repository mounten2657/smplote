# -*- coding: utf-8 -*-
"""
Gunicorn 生产环境配置
https://docs.gunicorn.org/en/stable/configure.html
gunicorn -c /www/server/gunicorn/conf/smplote.conf.py wsgi:app >/dev/null 2>&1 &
"""
import os
from datetime import datetime
from pathlib import Path
from gevent import monkey

monkey.patch_all()

# ---------------------------
# 基础配置
# ---------------------------
# 绑定地址和端口 (可配置多个)
bind = ['0.0.0.0:990']  # 可同时监听端口和Unix socket， 如 'unix:/tmp/gunicorn.sock'

# 工作进程数 (推荐: CPU核心数*2 + 1)
# import multiprocessing
# workers = multiprocessing.cpu_count() * 2 + 1
workers = 4

# Worker类型 (根据应用类型选择)
worker_class = 'gevent'  # 异步IO应用推荐: gevent/eventlet, CPU密集型: sync/gthread

# 每个worker的线程数 (仅对gthread/同步worker有效)
threads = 2

# 进程名称 (ps/top显示)
proc_name = 'gunicorn_app'

# 工作目录
chdir = '/www/wwwroot/smplote'

# ---------------------------
# 性能调优
# ---------------------------
# 每个worker的最大并发连接数
worker_connections = 1000

# 请求超时时间(秒)
timeout = 120

# 优雅关闭超时时间
graceful_timeout = 30

# worker处理指定请求后重启 (防止内存泄漏)
max_requests = 1000
max_requests_jitter = 50  # 随机抖动范围

# 预加载应用 (减少内存占用，但worker间不共享内存)
preload_app = True

# ---------------------------
# 安全配置
# ---------------------------
# 运行用户/组 (需要sudo权限)
user = 'www'
group = 'www'

# 文件权限掩码
umask = 0o007

# 请求数据大小限制 (防止DDoS)
limit_request_line = 4094  # 请求行最大字节
limit_request_fields = 100  # 请求头最大数量
limit_request_field_size = 8190  # 单个请求头最大字节

# ---------------------------
# 日志配置
# ---------------------------
# 访问日志 (None表示不记录，'-' 代表标准输出)
accesslog = f'/www/wwwlogs/gunicorn/app_access_{datetime.now().strftime("%Y-%m-%d")}.log'
# 错误日志 (必填，'-' 代表标准输出)
errorlog = '/www/wwwlogs/gunicorn/app_error.log'
# 日志级别 (debug/info/warning/error/critical)
loglevel = 'debug'
# 日志格式
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(L)s'

# 自动创建一下日志文件 - 目录自己先创建
Path(accesslog).touch(exist_ok=True)
Path(errorlog).touch(exist_ok=True)

# ---------------------------
# 高级配置
# ---------------------------
# 环境变量
raw_env = [
    'SMPLOTE_VERSION=v1.0.1',
]

# 代理模式 (当运行在Nginx后时需要)
proxy_protocol = True
forwarded_allow_ips = '*'  # 或指定IP如 '10.0.0.1,192.168.1.1'

# ---------------------------
# 调试配置 (生产环境不应启用)
# ---------------------------
# 代码变更自动重启 (仅开发用)
reload = False
# 打印所有执行语句 (极端调试)
spew = False
# 检查配置
check_config = False


# ---------------------------
# 自定义Hook (可选)
# ---------------------------
def post_fork(server, worker):
    """worker启动后执行"""
    os.environ.setdefault('PYTHON_RUN_MAIN', 'true')
    os.environ.setdefault('IS_PROD', 'true')
    os.environ.setdefault('REDIS_PORT_PROD', '6379')
    os.environ.setdefault('DB_MYSQL_PORT_PROD', '3306')
    server.log.info("Service has been successfully started, Worker is running ... ")


def when_ready(server):
    """服务启动完成时执行"""
    server.log.info("Server is ready. Spawning workers")


def worker_int(worker):
    """worker收到INT信号时执行"""
    worker.log.info("Worker received INT or QUIT signal")


def worker_abort(worker):
    """worker收到ABRT信号时执行"""
    worker.log.info("Worker received SIGABRT signal")

