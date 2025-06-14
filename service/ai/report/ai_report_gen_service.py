import os.path
from pathlib import Path
from typing import Optional, Union
from service.ai.ai_client_service import AiClientService
from model.wechat.sqlite.wx_core_model import WxCoreModel
from model.wechat.wechat_msg_model import WechatMsgModel
from tool.unit.img.md_to_img import MdToImg
from tool.core import Config, File, Str, Time, Dir


class AIReportGenService:
    """AI报告生成器"""

    @staticmethod
    def generate_report(
            g_user: dict,
            content: Union[str, Path],
            output_path: Optional[str] = None,
            prompt_type: str = 'simple',
            extra: dict = None,
    ) -> str:
        """
        生成并保存报告
        :param g_user: 群聊信息 - {"id": "xxx", "name": "xxx"}
        :param content: 聊天文本内容/聊天文本文件绝对路径
        :param output_path: 输出文件路径（.md格式）
        :param prompt_type: 指定AI prompt 模版类型: simple | detail
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
            text = Str.sub_str_len(text, 65435 - len(ai_config['report_prompt']['template']), 1)
        text = f"{ai_config['report_prompt']['template']}\n\n微信群[{g_user['name']}]聊天记录：\n\n{text}"
        prompt = ai_config['report_prompt'][prompt_type]

        # 2. 调用AI
        response, aid = AiClientService.answer(text, prompt, g_user, 'GEN_REP', extra)

        # 3. 保存结果
        if output_path:
            File.save_file(response, output_path, False)

        return response

    @staticmethod
    def get_report_img(data, p_type='simple', is_force=0):
        """获取总结图片"""
        g_wxid = data['g_wxid']
        g_user = {"id": g_wxid, "name": data['g_wxid_name']}
        fp = Dir.wechat_dir(f"room/{str(g_wxid).split('@')[0]}/{Time.date('%Y%m')}/file")
        os.makedirs(fp, exist_ok=True)
        fn_txt = f"{fp}/report_{Time.date('%Y%m%d')}.txt"
        fn_md = f"{fp}/report_{Time.date('%Y%m%d')}_{p_type}.md"
        fn_img = f"{fp}/report_{Time.date('%Y%m%d')}_{p_type}.png"
        if File.exists(fn_img) and not is_force:
            return fn_img
        if not Config.is_prod():
            return False
        # 获取内容
        text_list = []
        db = WechatMsgModel()
        m_list = db.get_msg_list(g_wxid)
        if not m_list:
            return False
        nl = '\r' if Config.is_prod() else '\n'
        for m in m_list:
            if 'revoke' == m['content_type']:
                continue
            m['content'] = m['content'] if int(m['pid']) else f"[AI助手]{m['content']}"
            text = f"{nl}[{m['msg_time']}] {m['s_wxid_name']} :{nl}{m['content']}{nl}"
            text_list.append(text)
            if len(''.join(text_list)) > 63000:
                break
        content = ''.join(reversed(text_list))
        File.save_file(content, fn_txt, False, False)
        # 生成md
        AIReportGenService.generate_report(g_user, fn_txt, fn_md, p_type, data)
        # md 转图片
        MdToImg.gen_md_img(fn_md, fn_img)
        return fn_img

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
        db = WxCoreModel()
        room_name = db.get_room_name(g_wxid)
        g_user = {"id": g_wxid, "name": room_name}
        if report_type != 2:
            # 简略版
            save_path[0] = out_path = Dir.abs_dir(base_dir + f'/{g_name}_{report_date}.md')
            res[0] = AIReportGenService.generate_report(g_user, content, out_path, 'simple')
        if report_type != 1:
            # 详细版
            save_path[1] = out_path = Dir.abs_dir(base_dir + f'/{g_name}_{report_date}_detail.md')
            res[1] = AIReportGenService.generate_report(g_user, content, out_path, 'detail')
        return {"save_path": save_path, "answer": [len(res[0]), len(res[1])]}
