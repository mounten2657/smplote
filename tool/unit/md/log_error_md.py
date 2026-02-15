import json
from datetime import datetime
from tool.core import Env, Http, Attr


class LogErrorMd:

    @staticmethod
    def get_error_markdown(result, log_id=None):
        """
        将错误结果转换为告警 Markdown 消息

        :param result: 错误数据结构 {
            "err_msg": ["error message"],
            "err_cause": ["current_exception", "original_exception"],
            "err_file_list": ["file:line", ...]
        }
        :param log_id: 可选日志追踪ID
        :return: 格式化后的 Markdown 字符串
        """
        # 处理可能为字符串类型的 err_msg
        error_message = result.get("err_msg", [])
        app_name = Env.get('APP_NAME', 'SMP')
        if isinstance(error_message, str):
            error_message = [error_message]
        error_message = [str(item) for item in error_message if item]  # 过滤 None
        http_err = ''
        if Http.is_http_request():
            http_url = Http.get_request_route()
            http_method = Http.get_request_method()
            http_data = json.dumps(Http.get_request_params())
            headers = Http.get_request_headers()
            user_agent = Attr.get(headers, 'User-Agent')
            ip = Http.get_client_ip()
            http_err += f"HTTP/2.0 - {http_method} - {http_url}\r\n"
            http_err += f"    └─ IP: {ip}\r\n"
            http_err += f"    └─ UA: {user_agent}\r\n"
            http_err += f"    └─ RAW: {http_data[:768]}"

        # 生成 Markdown 内容 ⚡🔥✈️💣⚠️❌
        markdown = f"""🔥 **{str(app_name).capitalize()} 系统异常告警**  

    ⚠️ **错误描述**  
    {" | ".join(error_message)}

    ⛔ **错误溯源**  
    ```
    {result.get('err_cause', ['', ''])[0]}
    └─ {result.get('err_cause', ['', ''])[1]}
    {http_err}
    ```

    🗂️ **代码位置**  
"""

        # 添加文件位置列表
        for file in result.get("err_file_list", []):
            markdown += f"     ▸ {file}\r\n"

        # 添加时间和操作建议
        markdown += f"""
    ⏰ **发生时间**  
     {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  

    📊 **错误自检**  
     完整日志追踪ID: <{log_id[:24] if log_id else 'None'}>
     """

        return markdown

