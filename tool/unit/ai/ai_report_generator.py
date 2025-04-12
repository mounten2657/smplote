import openai
import os.path
from pathlib import Path
from typing import Optional, Union
from tool.unit.ai.ai_client_manager import AIClientManager
from tool.core import *


class AIReportGenerator:
    """AI报告生成器"""

    def __init__(self, client_manager: AIClientManager):
        self.client = client_manager.get_client()
        self.config = client_manager.config

    def generate_report(
            self,
            content: Union[str, Path],
            output_path: Optional[str] = None,
            service: Optional[str] = None
    ) -> str:
        """
        生成并保存报告
        :param content: 文本内容/文件路径
        :param output_path: 输出文件路径（.md格式）
        :param service: 指定AI服务
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
        response = self._call_ai(text, service)

        # 3. 保存结果
        if output_path:
            File.save_file(response, output_path, False)

        return response

    def _call_ai(self, text: str, service: Optional[str] = None) -> str:
        """调用AI接口"""
        logger = Logger()
        logger.info({"service": service, "config": self.config, "content": text[0:100]}, 'CALL_AI_TXT', 'ai')
        try:
            client = self.client if not service else AIClientManager().get_client(service)
            response = client.chat.completions.create(
                model=self.config['services'][service or self.config['last_service']]['model'],
                messages=[
                    {"role": "system", "content": self.config['prompt']},
                    {"role": "user", "content": text}
                ],
                temperature=0.3
            )
            res = response.choices[0].message.content
            logger.info({"service": service, "content": res}, 'CALL_AI_RES', 'ai')
        except (Exception, openai.InternalServerError) as e:
            res = Error.handle_exception_info(e)
            logger.info({"service": service, "content": res}, 'CALL_AI_EXP', 'ai')
        return res

    @staticmethod
    def daily_report(g_wxid_dir: str, report_date: str):
        """
        静态方法生成日报
        :param g_wxid_dir: 群聊目录
        :param report_date: 报告日期 Ymd 格式
        :return: 生成的报告内容
        """
        manager = AIClientManager()
        generator = AIReportGenerator(manager)
        g_name = os.path.basename(g_wxid_dir)
        base_dir = g_wxid_dir + '/' + report_date
        content = Dir.abs_dir(base_dir + '/chat_list.txt')
        out_path = Dir.abs_dir(base_dir + f'/{g_name}_{report_date}.md')
        res = generator.generate_report(content, out_path)
        return {"out_path": out_path, "answer": res}



