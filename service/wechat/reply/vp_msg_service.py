from utils.wechat.vpwechat.vp_client import VpClient
from tool.core import Config, Attr, Time, Logger

logger = Logger()


class VpMsgService:

    morning_list = [
        '早安。晨光会把昨夜的褶皱熨平，新的一天，是给生活重新折纸的机会🌅',
        '清晨的风不疾不徐，像在说：慢慢来，那些你认真走过的路，都藏着未来的伏笔🍃',
        '推开窗，让第一缕阳光落在掌心——今日的美好，从接纳每一个当下开始✨',
        '早安。生活是种律动，须有光有影，有晴有雨，而今日的晨光，正是雨后天晴的序章🌦️',
        '露珠在叶尖打转，像未说出口的温柔。新的一天，愿你被世界温柔以待，也温柔待自己💧',
        '太阳慢慢爬上山头，像在教我们：所有的美好，都值得耐心等待🌞',
        '早安。昨日的烦恼是今天的伏笔，今日的晨光会把它酿成往后的甜🍯',
        '风穿过树梢，留下沙沙的诗行；你走过清晨，便成了今日最温柔的篇章🍂',
        '新的一天，像一张空白的宣纸，你笔下的每一笔认真，都是最动人的墨色🖌️',
        '早安。生活不是追逐终点的赛跑，而是带着花香散步的旅程，慢慢走，别错过沿途风景🌸',
        '晨光洒在窗台，像在轻声说：你不需要追赶别人的脚步，你的时区里，一切都刚刚好⏳',
        '清晨的雾霭会散去，就像心里的迷茫终会清晰。今日，愿你找到属于自己的方向🌫️',
        '早安。每一个清晨都是一次重生，你可以选择带着温柔，重新出发💫',
        '云朵在天空慢慢游走，像在演示：人生不必匆忙，偶尔停留，也是另一种风景☁️',
        '新的一天，把心比作容器吧——装满晨光，就容不下阴影；装满善意，便会遇见温柔❤️',
        '早安。露珠折射阳光，微小却明亮，就像你眼里的星光，足以照亮自己的小世界🌟',
        '晨光穿过枝叶的缝隙，落下细碎的光斑，像在说：生活的美好，藏在每一个小细节里🌿',
        '清晨的寂静里，藏着最纯粹的力量——新的一天，愿你能听见内心的声音，坚定前行🔇',
        '早安。日子是一帧一帧的风景，今日的晨光，是其中最温柔的一帧🌅',
        '风把昨夜的疲惫吹向远方，晨光把今日的希望铺在路上。愿你带着勇气，奔赴今日的晴朗💨',
        '新的一天，像一杯温热的茶——初尝或许平淡，细品便有回甘，慢慢来，总会尝到甜☕',
        '早安。月亮把未完的故事交给太阳，而你，也可以把未完成的遗憾，变成今日的新开始🌙',
        '晨光落在书页上，像在标注：所有的等待都有意义，所有的坚持都会开花📖',
        '清晨的花悄悄绽放，不声不响却自有力量。今日，愿你也能安静生长，自有光芒🌼',
        '早安。生活不是单选题，你可以选择温柔，选择坚定，选择把今日过成喜欢的样子🌈',
        '新的一天，把烦恼折成纸船，让晨光的溪流带它漂走，留下的，都是轻松与期待🚢',
        '晨光为大地披上薄纱，像在守护每一个未醒的梦。愿你今日的梦，都能慢慢实现🌞',
        '早安。风会记住花的香，时光会记住你的努力，今日的每一步，都在靠近更好的自己💐',
        '清晨的第一声鸟鸣，是自然的早安；你眼里的第一缕光，是自己的希望🐦',
        '新的一天，像一幅待填色的画，你用微笑作笔，用温柔作色，便是最美的风景🎨',
        '早安。所有的美好都不是突然降临，而是日复一日的积累——今日的你，比昨天更接近美好💫'
    ]

    welcome_list = [
        "欢迎新成员！祝玩好玩嗨玩出下一代，群里永远有你的快乐位置～",
        "热烈欢迎！咱群个个都是人才，说话又好听，来了的都不想走，以后多唠多互动呀～",
        "新成员入群啦！温馨提示：爆照极有可能触发群主发对象流程，快准备好你的美照帅照吧～",
        "欢迎新朋友！进群就是一家人，跑图有人陪，emo有人哄，福利还能一起冲～",
        "热烈欢迎新伙伴！群里没有冷场，只有唠不完的梗和等你一起蹭的图，快融入我们吧～",
        "新成员来啦！祝在群里早日找到合拍CP，每天都有好心情，群主的红包也不会少～",
        "欢迎加入大家庭！这里没有孤单，只有一群有趣的人陪你聊日常、闯快乐，以后多指教～",
        "新伙伴入群欢迎！进群即享：陪跑图不被丢，蹭福利不落后，还有一群逗比陪你走～",
        "欢迎新成员！愿你在群里每天都有新快乐，想吃肯德基有人约，想吐槽有人听～",
        "热烈欢迎新朋友！咱群主打一个温暖热闹，有困难大家帮，有快乐一起享，期待你的精彩～",
        "新成员来啦！祝在群里玩得尽兴，聊得开心，不管是唠嗑还是蹭图，都能找到同频的人～",
        "欢迎加入！进群就是缘分，以后一起分享日常，互蹭福利，群主的冷笑话也会按时送达哦～",
        "热烈欢迎新伙伴！群里藏着超多有趣灵魂，等你一起唠梗、跑图、盼福利，来了就别想走～",
        "欢迎新成员！愿你在群里收获快乐，结交好友，每天都能被温暖和笑声包围～",
        "新伙伴入群欢迎！进群福利已就位：陪聊、陪玩、陪吐槽，还有不定期惊喜，快开启你的群聊时光～"
    ]

    reason_list = [
        "群主没有发红包", "群主没有分配对象", "群主没有定期发放鸡蛋",
        "没有滴到对象", "缺乏关爱", "生某人的气了", "一怒之下怒了一下",
        "蹭不到图", "跑图被丢", "没有CP", "被冥龙创哭", "emo了", "想静静",
        "没有吃到肯德基", "山高路远江湖再见，且行且珍惜！",
        "听说隔壁群发奶茶，我去探探路", "隔壁群发CP了",
        "手机内存告急", "群聊暂存江湖",
        "群主三分钟没说话", "散伙先溜了",
        "被群里大佬卷到了", "退群偷偷练号",
        "妈妈喊吃饭", "回家吃晚饭",
        "爱情走了", "蓝瘦香菇",
        "退群冷静5分钟", "换小号装新人混红包",
        "群消息99+吓人", "先躲躲清净",
        "没有爆照，本颜狗先撤了",
        "被群主的冷笑话冻僵", "风紧扯呼",
        "江湖路远，下次发红包记得@我归队",
    ]

    @staticmethod
    def get_extra(t_wxid, ak):
        """整合额外信息"""
        client = VpClient(ak)
        config = Config.vp_config()
        app_config = config['app_list'][ak]
        self_wxid = app_config['wxid']
        a_g_wxid = config['admin_group']
        g_wxid = t_wxid if t_wxid else a_g_wxid
        s_wxid = self_wxid
        # 从缓存中获取基本信息
        if '@chatroom' in g_wxid:  # 群聊
            room = client.get_room(g_wxid)
            user = Attr.select_item_by_where(room.get('member_list', []), {"wxid": s_wxid}, {})
            s_wxid_name = user.get('display_name', '')
            g_wxid_name = room.get('nickname', '')
            g_wxid_head = room.get('head_img_url', '')
        else:  # 私聊
            user = client.get_user(t_wxid)
            g_user = client.get_user(g_wxid)
            s_wxid_name = user.get('nickname', '')
            g_wxid_name = g_user.get('nickname', '')
            g_wxid_head = g_user.get('head_img_url_small', '')
        extra = {"s_wxid": s_wxid, "s_wxid_name": s_wxid_name, "g_wxid": g_wxid, "g_wxid_name": g_wxid_name}
        return client, extra, g_wxid_head

    @staticmethod
    def vp_normal_msg(content, ats=None, t_wxid='', ak='a1', extra=None):
        """
        发送普通群消息

        :param content:  发送的内容
        :param ats:  需要艾特的人 - [{"wxid": "xxx", "nickname": "yyy"}]
        :param t_wxid:  发送给谁 - 群聊wxid或人的wxid
        :param ak:  app_key
        :param extra:  额外信息
        :return:
        """
        client, g_extra, g_head = VpMsgService.get_extra(t_wxid, ak)
        ats = ats if ats else []
        extra = extra if extra else g_extra
        return client.send_msg(content, t_wxid, ats, extra)

    @staticmethod
    def vp_card_msg(title, des, head='', url='#', t_wxid='', ak='a1', extra=None):
        """
        发送卡片消息

        :param title:  卡片的标题 - 尽可能的简短
        :param des:  卡片的正文 - 支持换行符
        :param head:  卡片右侧头像
        :param url:  卡片的跳转链接
        :param t_wxid:  发送给谁 - 群聊wxid或人的wxid
        :param ak:  app_key
        :param extra:  额外信息
        :return:
        """
        client, g_extra, g_head = VpMsgService.get_extra(t_wxid, ak)
        extra = extra if extra else g_extra
        res = {
            "title": title,
            "des": des,
            "url": url,
            "thumb": head if head else g_head,
        }
        return client.send_card_message(res, t_wxid, extra)

    @staticmethod
    def vp_morning(t_wxid='', ak='a1'):
        """发送早安消息"""
        morning = Attr.random_choice(VpMsgService.morning_list)
        return VpMsgService.vp_normal_msg(morning, None, t_wxid, ak)

    @staticmethod
    def vp_redmind(s_wxid, g_wxid, ak='a1'):
        """发送红包提醒"""
        if s_wxid:  # 先屏蔽吧，没什么人用
            return False
        client = VpClient(ak)
        s_user = client.get_user(s_wxid)
        s_name = s_user.get('nickname', '')
        s_head = s_user.get('head_img_url_small', '')
        title = "【红包提醒】"
        des = f"[{s_name} {Time.date('%H:%M')} 发送红包]\r\n"
        des += f"[@艾特位招租]"
        return VpMsgService.vp_card_msg(title, des, s_head, '#', g_wxid, ak)

    @staticmethod
    def vp_join_room(u_wxid, u_name, g_wxid, ak='a1'):
        """发送入群提醒"""
        client = VpClient(ak)
        title = "【欢迎新成员】"
        des = f"昵称：{u_name}\r\n"
        des += f"时间：{Time.date()}"
        # 查询用户信息
        t_user = client.get_user(u_wxid)
        t_head = t_user.get('head_img_url_small', '')
        VpMsgService.vp_card_msg(title, des, t_head, '#', g_wxid, ak)
        # 发送欢迎语 + 群备注
        welcome = Attr.random_choice(VpMsgService.welcome_list)
        g_remark = client.get_room_grp_rmk(g_wxid)
        welcome += f"\r\n\r\n{g_remark}" if g_remark else ''
        return VpMsgService.vp_normal_msg(welcome, [{"wxid": u_wxid, "nickname": u_name}], g_wxid, ak)

    @staticmethod
    def vp_change_name(b_name, a_name, c_head, g_wxid, ak='a1'):
        """发送马甲提醒"""
        title = f"【马甲变更】"
        des = f"旧昵称：{b_name}\r\n"
        des += f"新昵称：{a_name}"
        logger.error(f"{title} - {des}", 'ROOM_CHANGE_NAME')
        return VpMsgService.vp_card_msg(title, des, c_head, '#', g_wxid, ak)

    @staticmethod
    def vp_quit_room(u_name, c_head, g_wxid, ak='a1'):
        """发送退群提醒"""
        reason = Attr.random_choice(VpMsgService.reason_list)
        title = '【退群提醒】'
        des = f"成员：{u_name} {Time.date('%H:%M')} 退群\r\n"
        des += f"原因：{reason}"
        return VpMsgService.vp_card_msg(title, des, c_head, '#', g_wxid, ak)
