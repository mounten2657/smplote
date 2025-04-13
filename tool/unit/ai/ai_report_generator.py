import os.path
from pathlib import Path
from typing import Optional, Union
from tool.unit.ai.ai_client_manager import AIClientManager
from tool.core import *


class AIReportGenerator:
    """AI报告生成器"""

    def __init__(self):
        self.client = AIClientManager()
        self.config = self.client.config

    @staticmethod
    def generate_report(
            content: Union[str, Path],
            output_path: Optional[str] = None,
            prompt: str = 'prompt',
            service: Optional[str] = 'DeepSeek'
    ) -> str:
        """
        生成并保存报告
        :param content: 文本内容/文件路径
        :param output_path: 输出文件路径（.md格式）
        :param prompt: 指定AI prompt: prompt | prompt_detail
        :param service: 指定AI服务，默认 DeepSeek
        :return: 生成的报告内容
        """
        # 1. 获取内容
        if os.path.exists(content):
            text = File.read_file(content)
        else:
            text = content
        if not text:
            return "未获取到文本内容，请检查配置项"

        # 2. 调用AI
        client = AIClientManager()
        prompt = client.config[prompt]
        response = client.call_ai(text, prompt, service)

        # 3. 保存结果
        if output_path:
            File.save_file(response, output_path, False)

        return response

    @staticmethod
    def daily_report(g_wxid_dir: str, params: dict):
        """
        静态方法生成日报 - 简略版 | 详细版
        :param g_wxid_dir: 群聊目录
        :param params: 请求入参，包含所有请求参数
        :return: 生成的报告内容
        """
        # 默认今天
        start_time, end_time = Time.start_end_time_list(params)
        report_date = Time.dft(end_time if end_time else Time.now(), '%Y%m%d')
        report_type = int(params.get('report_type', '1'))  # 默认生成简略版 - 0:全部1:简略版|2:详细版
        g_name = os.path.basename(g_wxid_dir)
        base_dir = g_wxid_dir + '/' + report_date
        content = Dir.abs_dir(base_dir + '/chat_list.txt')
        res = save_path = ['f1', 'f2']
        if report_type != 2:
            # 简略版
            save_path[0] = out_path = Dir.abs_dir(base_dir + f'/{g_name}_{report_date}.md')
            res[0] = AIReportGenerator.generate_report(content, out_path)
        if report_type != 1:
            # 详细版
            save_path[1] = out_path = Dir.abs_dir(base_dir + f'/{g_name}_{report_date}_detail.md')
            res[1] = AIReportGenerator.generate_report(content, out_path, 'prompt_detail')
        return {"save_path": save_path, "answer": [len(res[0]), len(res[1])]}



