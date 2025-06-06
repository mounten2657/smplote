from service.ai.ai_client_service import AiClientService
from tool.core import Dir, File


class AiCommandService:

    @staticmethod
    def question(content, user, biz_code, extra=None):
        """AI 提问"""
        content = str(content).replace('#提问', '').strip()
        if not content or content == 'None':
            text = '请按 "#提问" 开头进行AI聊天，如：\r\n#提问 请推荐三首纯音乐'
            return text, 0
        prompt = '你是一个智能助手，请帮我回答一系列的问题，回答要简短有力，条理清晰，不要过度联想，语气要温和。'
        response, aid = AiClientService.answer(content, prompt, user, biz_code, extra)
        response = f"{response}\r\n\r\n--此内容由AI生成，请仔细甄别--"
        return response, aid

    @staticmethod
    def science(content, user, biz_code, extra=None):
        """AI 百科"""
        content = str(content).replace('#百科', '').strip()
        if not content or content == 'None':
            text = '请按 "#百科" 开头进行AI科普，如：\r\n#百科 蝾螈'
            return text, 0
        prompt = '你是一个科普助手，请根据我提供的关键词进行科普，回答要简短有力，条理清晰，语气要严谨。'
        response, aid = AiClientService.answer(content, prompt, user, biz_code, extra)
        response = f"{response}\r\n\r\n--此内容由AI生成，请仔细甄别--"
        return response, aid

    @staticmethod
    def bf(content, user, biz_code, extra=None):
        """AI 男友"""
        content = str(content).replace('#男友', '').strip()
        if not content or content == 'None':
            content = '你好'
        prompt = File.read_file(Dir.abs_dir('storage/upload/wechat/website/sky/prompt/bf_01.txt'))
        response, aid = AiClientService.answer(content, prompt, user, biz_code, extra)
        response = f"{response}\r\n\r\n--此内容由AI生成，请仔细甄别--"
        return response, aid

    @staticmethod
    def gf(content, user, biz_code, extra=None):
        """AI 女友"""
        content = str(content).replace('#女友', '').strip()
        if not content or content == 'None':
            content = '你好'
        prompt = File.read_file(Dir.abs_dir('storage/upload/wechat/website/sky/prompt/gf_01.txt'))
        response, aid = AiClientService.answer(content, prompt, user, biz_code, extra)
        response = f"{response}\r\n\r\n--此内容由AI生成，请仔细甄别--"
        return response, aid
