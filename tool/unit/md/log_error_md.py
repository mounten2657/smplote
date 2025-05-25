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
        http_url = http_method = http_data = 'None'
        user_agent = ip = 'None'
        if Http.is_http_request():
            http_url = Http.get_request_route()
            http_method = Http.get_request_method()
            http_data = json.dumps(Http.get_request_params())
            headers = Http.get_request_headers()
            user_agent = Attr.get(headers, 'User-Agent')
            ip = Http.get_client_ip()

        # 生成 Markdown 内容 ⚡🔥✈️💣⚠️❌
        markdown = f"""🔥 **{str(app_name).capitalize()} 系统异常告警**  

    ⚠️ **错误描述**  
    {"\r\n".join(error_message)}

    ⛔ **错误溯源**  
    ```
    {result.get('err_cause', ['', ''])[0]} (触发异常)  
    └─ {result.get('err_cause', ['', ''])[1]} (原始异常)  
    HTTP/2.0 - {http_method} - {http_url}
    └─ {user_agent} - {ip}
    └─ {http_data[:768]}
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

    📊 **操作建议**  
     1. 检查 `{result.get('err_cause', ['', ''])[-1]}` 相关逻辑  
     2. 验证 {result.get('err_file_list', [''])[0] if result.get('err_file_list') else 'N/A'} 行代码逻辑  
     """

        # 可选日志ID
        if log_id:
            markdown += f"3. 查看完整日志追踪ID: <{log_id[:24]}>\r\n"

        return markdown

