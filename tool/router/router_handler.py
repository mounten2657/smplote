import os
import logging
import threading
import webbrowser
from flask import Response
from flask import Flask, request, send_from_directory
from tool.router.parse_handler import ParseHandler
from tool.core import Logger, Attr, Api, Dir, Config, Error, Http, Env
from utils.wechat.qywechat.qy_client import QyClient
from service.source.preview.file_preview_service import FilePreviewService

logger = Logger()


class RouterHandler:

    # 免鉴权的开放接口
    OPEN_ROUTE_LIST = [
        'bot/index/index',
        'callback/gitee_callback/smplote',
    ]

    # 路由忽略列表，适合回调和文件预览等
    IGNORE_ROUTE_LIST = [
        'callback/qy_callback/collect_wts',
        'callback/qy_callback/collect_gpl',
        'src/static/image',
        'src/static/file',
        'src/terminal/output',
    ]

    # 日志忽略列表，屏蔽高频率且无用的接口
    IGNORE_LOG_LIST = [
        'src/terminal/output',
    ]

    def __init__(self):
        self.app = Flask(__name__, template_folder=Dir.abs_dir('data/static/html'))
        self.config = Config.app_config()
        self.close_filter_log()
        self.setup_routes()

    def setup_routes(self):
        # 开始请求之前的动作
        @self.app.before_request
        def before_request():
            request_url = request.url
            request_params = self.get_http_params()
            if not any(route in request_url for route in self.IGNORE_LOG_LIST):
                logger.info(data={"request": {"url": request_url, "request_params": request_params}}, msg="START")

        # 定义首页默认路由
        @self.app.route('/', defaults={'path': ''})
        @self.app.route('/<path:path>')
        def index(path):
            if path in ('', 'index', 'index.html', 'index.php', 'index.py'):
                path = self.config.get('APP_INDEX')
            return http_execute_method(path)

        # 图片资源访问
        @self.app.route('/src/static/image/<path:path>')
        def image_file(path):
            return FilePreviewService.image(path)

        # 文件资源访问
        @self.app.route('/src/static/file/<path:path>')
        def office_file(path):
            return FilePreviewService.file(path)

        # 定义图标路径
        @self.app.route('/favicon.ico')
        def favicon():
            return send_from_directory(Dir.abs_dir('data/static/icon'), 'favicon.ico',
                                       mimetype='image/vnd.microsoft.icon')

        # 定义路由解析
        @self.app.route('/<path:method_path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])
        def http_execute_method(method_path):
            try:
                # API 鉴权
                headers = Http.get_request_headers()
                authcode = Attr.get(headers, 'Authcode')
                open_list = self.OPEN_ROUTE_LIST + self.IGNORE_ROUTE_LIST
                if Env.get('APP_AUTH_KEY') != authcode and method_path not in open_list:
                    return Api.error('Permission denied', None, 99)
                module_name, method_name = method_path.rsplit('/', 1)
                module_path = f'{module_name.replace("/", ".")}'
                params = RouterHandler.get_http_params()
                result = ParseHandler.execute_method(module_path + '.' + method_name, params)
                # 判断是否有异常
                if Error.has_exception(result):
                    return Api.error(f"{result['err_msg'][0]}", Attr.remove_keys(result, ['err_msg', 'err_file_list']))
                # 特定路由直接放行
                if method_path in self.IGNORE_ROUTE_LIST:
                    return result
                else:
                    return Api.success(result)
            except Exception as e:
                err = Error.handle_exception_info(e)
                logger.error(err, 'APP_PARSE_ROUTE_ERR')
                QyClient().send_error_msg(err, logger.uuid)   # 发送告警消息
                return Api.error(f"Method Not Found!", None, 500)

        # 请求完成后的动作
        @self.app.after_request
        def after_request(response):
            # response.direct_passthrough = False
            status_code = response.status_code
            response_result = None
            request_url = request.url
            try:
                response_result = Attr.parse_json_ignore(response.get_data(as_text=True))
            except RuntimeError as e:
                # err = Error.handle_exception_info(e)
                # logger.info(data={"response": {"status_code": status_code, "response_result": err}}, msg="EXP")
                pass
            if not any(route in request_url for route in self.IGNORE_LOG_LIST):
                logger.info(data={"response": {"status_code": status_code, "response_result": response_result}}, msg="END")
            return response

    @staticmethod
    def get_http_params():
        return Http.get_request_params()

    @staticmethod
    def get_method_name():
        """获取当前请求的接口方法名"""
        module, method_name = request.base_url.rsplit('/', 1)
        return method_name

    def close_filter_log(self):
        # 关闭 Werkzeug 默认的访问日志
        werkzeug_log = logging.getLogger('werkzeug')
        werkzeug_log.setLevel(logging.ERROR)
        ignore_list = self.IGNORE_LOG_LIST

        # 只对特定的路由进行日志屏蔽
        class SSELogFilter(logging.Filter):
            def filter(self, record):
                return not any(route in record.getMessage() for route in ignore_list)

        werkzeug_log.addFilter(SSELogFilter())
        return True

    @staticmethod
    def open_browser(url):
        if not os.environ.get("WERKZEUG_RUN_MAIN"):
            # webbrowser.open_new(url)
            return True

    def init_app(self):
        """初始化app"""
        return ParseHandler.init_program()

    def prod_app(self):
        """正式环境启动"""
        self.init_app()
        return self.app

    def run_app(self):
        """本地环境启动"""
        self.init_app()
        if self.config.get('APP_OPEN_URL'):
            host_name = self.config.get("SERVER_HOST")
            host_name = 'localhost' if host_name == '0.0.0.0' else host_name
            url = f'http://{host_name}:{self.config.get("SERVER_PORT")}/{self.config.get("APP_OPEN_URL")}'
            threading.Timer(1, lambda: self.open_browser(url)).start()
        self.app.run(host=self.config.get("SERVER_HOST"), port=self.config.get("SERVER_PORT"),
                     debug=self.config.get("DEBUG"), threaded=True)
