from utils.ai.client.ai_client_manager import AIClientManager
from model.ai.ai_chat_model import AiChatModel
from model.ai.ai_context_model import AiContextModel
from tool.core import Time


class AiClientService:

    @staticmethod
    def answer(content, prompt, user, biz_code, extra=None):
        """
        发起 AI 问答 - 统一入口
        :param content:  提问文本
        :param prompt:  预设 prompt （用来设定角色）- 键名 或 自定义文本
        :param user:  提问用户的信息，如 wx.wxid, qy.userid 等 - {"id": 101, "name": "xxx"}
        :param biz_code:  业务代码
        :param extra:  额外参数
        :return:
        """
        client = AIClientManager()
        service = client.config['last_service']
        if biz_code in ['VP_QUS', 'VP_SCI']:  # 群聊使用免费的web ai
            service = 'WebGpt'
        ai_config = client.config['services'][service]
        t_config = {"ai_type": service, "ai_model": ai_config['model']}
        # 获取预设文本
        prompt_text = client.config.get(prompt)
        prompt_text = prompt_text if prompt_text else prompt
        # 对话入库
        cdb = AiChatModel()
        tdb = AiContextModel()
        chat = cdb.get_chat_info(user['id'], biz_code)
        cid = chat.get('id', 0) if chat else 0
        is_new = 0
        if not chat:
            is_new = 1
            cid = cdb.add_chat({
                "biz_code": biz_code,
                "user_id": user['id'],
                "user_name": user['name'],
                "chat_name": Time.date("%Y%m%d") + f"_{user['id']}",
                "extra": extra if extra else {},
            }, t_config)
        if not cid:
            return '', 0
        # 获取对话文本
        context_list = tdb.get_context_list(cid, biz_code)
        messages = [{"role": "system", "content": prompt_text}]  # 角色设定
        messages = AiClientService.get_chat_messages(context_list, messages, content)
        # 插入新对话
        tid = tdb.add_context({
            "chat_id": cid,
            "biz_code": biz_code,
            "method_name": 'ANS',
            "request_params": {"content": content, "messages": messages, "extra": extra if extra else {}},
            "is_summary": 0
        }, t_config)
        rid = 0
        start_time = Time.now(0)
        if 'WebGpt' == service:
            # 调用 web ai 接口
            if is_new:
                content = f"{prompt}\r\n现在，请直接回答问题：{content}"
            ret = client.call_ai_web(content, service, {"rid": extra.get('s_wxid', '')})
            if isinstance(ret, dict):
                rid = ret.get('room')
                response = ret.get('msg')
            else:
                response = str(ret)
        else:
            # 调用 openai 接口
            response = client.call_ai(messages)
        # 更新对话结果
        if response and isinstance(response, str):
            response_result = {"content": response}
            if rid:
                response_result.update({"rid": rid})
            update_data = {
                "is_succeed": 1,
                "response_result": response_result,
                "response_time": round(Time.now(0) - start_time, 3) * 1000
            }
            tdb.update_context_response(tid, update_data)
            count = tdb.get_context_count(cid, biz_code)
            # 更新对话次数
            if count:
                cdb.update_chat_summary(cid, {"chat_count": count})
        return response, tid

    @staticmethod
    def get_chat_messages(context_list, messages, content):
        """获取历史对话列表 - 待优化 - 使用历史总结"""
        if not context_list:
            messages.append({"role": "user", "content": content})
            return messages
        for context in reversed(context_list):
            messages.append({"role": "user", "content": context['request_params']['content']})
            messages.append({"role": "assistant", "content": context['response_result']['content']})
            if len(messages) > 10:
                messages.pop(1)
                messages.pop(1)
        messages.append({"role": "user", "content": content})
        return messages
