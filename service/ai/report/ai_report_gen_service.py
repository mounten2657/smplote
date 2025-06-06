import os.path
from pathlib import Path
from typing import Optional, Union
from service.ai.ai_client_service import AiClientService
from model.wechat.sqlite.wx_core_model import WxCoreModel
from tool.core import Config, File, Str, Time, Dir


class AIReportGenService:
    """AI报告生成器"""

    @staticmethod
    def generate_report(
            g_user: dict,
            content: Union[str, Path],
            output_path: Optional[str] = None,
            prompt: str = 'prompt',
            extra: dict = None,
    ) -> str:
        """
        生成并保存报告
        :param g_user: 群聊信息
        :param content: 文本内容/文件路径
        :param output_path: 输出文件路径（.md格式）
        :param prompt: 指定AI prompt: prompt | prompt_detail
        :param extra: 额外参数
        :return: 生成的报告内容
        """
        # 1. 获取内容
        if os.path.exists(content):
            text = File.read_file(content)
        else:
            text = content
        if not text:
            return "未获取到文本内容，请检查配置项"

        ai_config = Config.ai_config()
        if ai_config['last_service'] == 'DeepSeek':
            text = Str.sub_str_len(text, 65435 - len(ai_config['report_template']), 1)
        db = WxCoreModel()
        room_name = db.get_room_name(g_user['id'])
        g_user['name'] = room_name
        text = f"{ai_config['report_template']}\n\n微信群[{room_name}]聊天记录：\n\n{text}"

        # 2. 调用AI
        response, aid = AiClientService.answer(text, prompt, g_user, 'GEN_REP', extra)

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
        g_wxid = params.get('g_wxid')
        base_dir = g_wxid_dir + '/' + report_date
        content = Dir.abs_dir(base_dir + '/chat_list.txt')
        res = save_path = ['f1', 'f2']
        g_user = {"id": g_wxid, "name": g_name}
        if report_type != 2:
            # 简略版
            save_path[0] = out_path = Dir.abs_dir(base_dir + f'/{g_name}_{report_date}.md')
            res[0] = AIReportGenService.generate_report(g_wxid, content, out_path)
        if report_type != 1:
            # 详细版
            save_path[1] = out_path = Dir.abs_dir(base_dir + f'/{g_name}_{report_date}_detail.md')
            res[1] = AIReportGenService.generate_report(g_user, content, out_path, 'prompt_detail')
        return {"save_path": save_path, "answer": [len(res[0]), len(res[1])]}
