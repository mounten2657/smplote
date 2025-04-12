from flask import Flask, request, send_from_directory
from .parse_handler import ParseHandler
from tool.core.logger import Logger
from tool.core.attr import Attr
from tool.core.api import Api
from tool.core.dir import Dir
from tool.core.config import Config
from tool.core.error import Error

logger = Logger()


class RouterHandler:
    def __init__(self):
        self.app = Flask(__name__)
        self.config = Config.app_config()
        self.setup_routes()

    def setup_routes(self):
        # 开始请求之前的动作
        @self.app.before_request
        def before_request():
            request_url = request.url
            request_params = dict(request.args)
            logger.info(data={"request":{"url": request_url, "request_params": request_params}}, msg="START")

        # 定义首页默认路由
        @self.app.route('/', defaults={'path': ''})
        @self.app.route('/<path:path>')
        def index(path):
            if path in ('', 'index', 'index.html', 'index.php', 'index.py'):
                path = self.config.get('APP_INDEX')
            return http_execute_method(path)

        # 定义图标路径
        @self.app.route('/favicon.ico')
        def favicon():
            return send_from_directory(Dir.abs_dir('data/static/icon'), 'favicon.ico',
                                       mimetype='image/vnd.microsoft.icon')

        # 定义路由解析
        @self.app.route('/<path:method_path>', methods=['GET', 'POST'])
        def http_execute_method(method_path):
            try:
                module_name, method_name = method_path.rsplit('/', 1)
                module_path = f'{module_name.replace("/", ".")}'
                params = RouterHandler.get_http_params()
                result = ParseHandler.execute_method(module_path + '.' + method_name, params)
                # 判断是否有异常
                if Error.has_exception(result):
                    return Api.error(f"{result['err_msg'][0]}", Attr.remove_keys(result, ['err_msg', 'err_file_list']))
                return Api.success(result)
            except (ImportError, AttributeError) as e:
                return f"Method Not Found! {e}", 500

        # 请求完成后的动作
        @self.app.after_request
        def after_request(response):
            status_code = response.status_code
            response_result = Attr.parse_json_ignore(response.get_data(as_text=True))
            logger.info(data={"response": {"status_code": status_code, "response_result": response_result}}, msg="END")
            return response

    @staticmethod
    def get_http_params():
        return request.args.to_dict()

    def run_app(self):
        self.app.run(host=self.config.get("SERVER_HOST"), port=self.config.get("SERVER_PORT"),
                     debug=self.config.get("DEBUG"))
