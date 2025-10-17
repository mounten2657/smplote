import time
import random
from service.ai.command.ai_command_service import AiCommandService
from service.sky.sky_data_service import SkyDataService
from service.ai.report.ai_report_gen_service import AIReportGenService
from tool.unit.song.music_search_client import MusicSearchClient
from tool.db.cache.redis_client import RedisClient
from utils.wechat.qywechat.qy_client import QyClient
from utils.wechat.vpwechat.vp_client import VpClient
from tool.core import Config, Attr, Sys, Dir, Transfer, Time


class VpCommandService:

    def __init__(self, app_key, g_wxid='', s_wxid=''):
        self.app_key = app_key
        self.client = VpClient(self.app_key)
        self.config = Config.vp_config()
        self.app_config = self.config['app_list'][self.app_key]
        self.self_wxid = self.app_config['wxid']
        self.a_g_wxid = self.config['admin_group']
        self.g_wxid = g_wxid if g_wxid else self.a_g_wxid
        self.s_wxid = s_wxid if s_wxid else self.self_wxid
        room = self.client.get_room(self.g_wxid)
        user = Attr.select_item_by_where(room.get('member_list', []), {"wxid": self.s_wxid}, {})
        self.s_wxid_name = user.get('display_name', '')
        self.g_wxid_name = room.get('nickname', '')
        self.g_wxid_count = int(room.get('member_count', 0))
        self.g_wxid_head = room.get('head_img_url', '')
        self.s_user = {"id": self.s_wxid, "name": self.s_wxid_name}
        self.at_list = [{"wxid": self.s_wxid, "nickname": self.s_wxid_name}]
        self.extra = {"s_wxid": self.s_wxid, "s_wxid_name": self.s_wxid_name, "g_wxid": self.g_wxid, "g_wxid_name": self.g_wxid_name}
        user = Attr.select_item_by_where(room.get('member_list', []), {"wxid": self.self_wxid})
        self.self_wxid_name = user.get('display_name', '')
        self.extra.update({"self_wxid": self.self_wxid, "self_wxid_name": self.self_wxid_name})
        self.is_admin = self.s_wxid in str(self.config['admin_list']).split(',')
        self.service = SkyDataService()

    def vp_manual(self, content):
        """入口"""
        c_str = """✨欢迎使用
        
    📢 可用命令列表：
    
    【基础功能】
    #提问 或 [101] - 智能问答
    #百科 或 [102]  - 知识百科

    【光遇专区】
    #任务 或 [201] - 每日任务查询
    #红石 或 [202] - 红石掉落时间
    #身高 或 [203] - 身高预测计算
    #日历 - 季节日历查询
    #先祖 - 旅行先祖查询
    #代币 - 活动代币查询
    #季蜡 - 每日季蜡位置
    #大蜡 - 每日大蜡位置
    #魔法 - 每日免费魔法
    #公告 - 游戏最新公告

    【休闲娱乐】
    #新闻 - 每日新闻查询
    #天气 - 实时天气查询
    #文案 - 获取朋友圈文案
    #v50 - 来个疯狂星期四
    #壁纸 - 随机精美壁纸
    #男友 - 虚拟男友聊天(内测中)
    #女友 - 虚拟女友聊天(内测中)
    #唱歌 - 随机歌曲
    #点歌 - 点播歌曲

    【管理员专用】
    #设置 - 系统设置
    #总结 - 群聊总结报告

    💡 提示：直接发送对应指令即可使用功能
    （如发送 "#任务" 查询任务）
    
    ⚡紧急联系：
    呼叫人工服务：直接输入 [103]（需@机器人触发）
        
        """
        response = c_str
        return self.client.send_msg(response, self.g_wxid, [], self.extra)

    def vp_question(self, content):
        """AI问答"""
        redis = RedisClient()
        cache_key = 'LOCK_AI_VP_QUS'
        if redis.get(cache_key, [self.s_wxid]) and not self.is_admin:
            response, aid = '每分钟只能提问一次', 0
        else:
            redis.set(cache_key, 1, [self.s_wxid])
            content = '#提问' if '101' == content else content
            response, aid = AiCommandService.question(content, self.s_user, 'VP_QUS', self.extra)
        self.extra.update({"aid": aid})
        return self.client.send_msg(response, self.g_wxid, self.at_list, self.extra)

    def vp_science(self, content):
        """AI百科"""
        redis = RedisClient()
        cache_key = 'LOCK_AI_VP_QUS'
        if redis.get(cache_key, [self.s_wxid]) and not self.is_admin:
            response, aid = '每分钟只能百科一次', 0
        else:
            redis.set(cache_key, 1, [self.s_wxid])
            content = '#百科' if '102' == content else content
            response, aid = AiCommandService.science(content, self.s_user, 'VP_SCI', self.extra)
        self.extra.update({"aid": aid})
        return self.client.send_msg(response, self.g_wxid, self.at_list, self.extra)

    def vp_bf(self, content):
        """AI男友"""
        response, aid = AiCommandService.bf(content, self.s_user, 'VP_BF', self.extra)
        self.extra.update({"aid": aid})
        return self.client.send_msg(response, self.g_wxid, self.at_list, self.extra)

    def vp_gf(self, content):
        """AI女友"""
        response, aid = AiCommandService.gf(content, self.s_user, 'VP_GF', self.extra)
        self.extra.update({"aid": aid})
        return self.client.send_msg(response, self.g_wxid, self.at_list, self.extra)

    def vp_self(self, content):
        """转人工"""
        QyClient(self.app_key).send_msg(f'{self.s_wxid_name} 正在呼唤你，请尽快回复')
        response = '已发送至管理员……\r\n\r\n正在呼唤本人，请稍后……'
        r_num = random.randint(1, 24)
        file = self.service.get_sky_file('yj', {"r_num": r_num})
        fp = file.get('save_path')
        if fp:
            fp = Dir.wechat_dir(f'{fp}')
            self.extra.update({"file": file})
            Sys.delayed_task(lambda: self.client.send_voice_message(fp, self.g_wxid, self.extra), delay_seconds=15)
        return self.client.send_msg(response, self.g_wxid, self.at_list, self.extra)

    def vp_sky_rw(self, content=''):
        """sky任务"""
        content = '#任务' if '201' == content else content
        file = self.service.get_sky_file('rw')
        fp = file.get('save_path')
        if fp:
            fp = Dir.wechat_dir(f'{fp}')
            self.extra.update({"file": file})
            self.client.send_img_msg(fp, self.g_wxid, self.extra)
            # 其它相关信息也一并发送
            jl = self.service.get_sky_file('jl')
            self.extra.update({"file": jl})
            self.client.send_img_msg(Dir.wechat_dir(f'{jl['save_path']}'), self.g_wxid, self.extra)
            dl = self.service.get_sky_file('dl')
            self.extra.update({"file": dl})
            self.client.send_img_msg(Dir.wechat_dir(f'{dl['save_path']}'), self.g_wxid, self.extra)
            mf = self.service.get_sky_file('mf')
            self.extra.update({"file": mf})
            self.client.send_img_msg(Dir.wechat_dir(f'{mf['save_path']}'), self.g_wxid, self.extra)
            return True
        response = '获取sky任务失败'
        return self.client.send_msg(response, self.g_wxid, self.at_list, self.extra)

    def vp_sky_hs(self, content='', is_week=0):
        """sky红石"""
        content = '#红石' if '202' == content else content
        if is_week and Time.week() < 5:
            return False
        file = self.service.get_sky_file('hs')
        fp = file.get('save_path')
        if not fp:
            # 重试一次
            time.sleep(5)
            file = self.service.get_sky_file('hs')
            fp = file.get('save_path')
        if fp:
            fp = Dir.wechat_dir(f'{fp}')
            self.extra.update({"file": file})
            return self.client.send_img_msg(fp, self.g_wxid, self.extra)
        response = '获取sky红石失败'
        return self.client.send_msg(response, self.g_wxid, self.at_list, self.extra)

    def vp_sky_sg(self, content):
        """sky身高"""
        redis = RedisClient()
        cache_key = 'LOCK_SKY_API_SG'
        if redis.get(cache_key, [self.s_wxid]) and not self.is_admin:
            return self.client.send_msg('每分钟只能查询身高一次', self.g_wxid, self.at_list, self.extra)
        content = '#身高' if '203' == content else content
        code = str(content).replace('#身高', '').strip()
        if len(code) < 14:
            response = '请输入"#身高 [好友码]"进行查询，如： #身高 B1A9-KMV2-4ZG5'
        elif self.g_wxid_count > 50:
            response = '只有管理员才能使用该功能'
        else:
            s_res = self.service.get_sky_sg(code)
            response = s_res.get('main', "暂未查询到身高")
        return self.client.send_msg(response, self.g_wxid, self.at_list, self.extra)

    def vp_sky_gg(self, content):
        """sky公告"""
        s_res = self.service.get_sky_gg()
        response = s_res.get('main', "暂未查询到公告")
        return self.client.send_msg(response, self.g_wxid, [], self.extra)

    def vp_sky_rl(self, content):
        """sky日历"""
        file = self.service.get_sky_file('rl')
        fp = file.get('save_path')
        if fp:
            fp = Dir.wechat_dir(f'{fp}')
            self.extra.update({"file": file})
            self.client.send_img_msg(fp, self.g_wxid, self.extra)
            # 其它相关信息也一并发送
            text = self.service.get_sky_djs()
            return self.client.send_msg(text['main'], self.g_wxid, [], self.extra)
        response = '暂未查询到日历'
        return self.client.send_msg(response, self.g_wxid, [], self.extra)

    def vp_sky_xz(self, content):
        """sky先祖"""
        file = self.service.get_sky_file('xz')
        fp = file.get('save_path')
        if fp:
            fp = Dir.wechat_dir(f'{fp}')
            self.extra.update({"file": file})
            return self.client.send_img_msg(fp, self.g_wxid, self.extra)
        response = '暂未查询到先祖'
        return self.client.send_msg(response, self.g_wxid, [], self.extra)

    def vp_sky_db(self, content):
        """sky代币"""
        file = self.service.get_sky_file('db')
        fp = file.get('save_path')
        if fp:
            fp = Dir.wechat_dir(f'{fp}')
            self.extra.update({"file": file})
            return self.client.send_img_msg(fp, self.g_wxid, self.extra)
        response = '暂未查询到代币'
        return self.client.send_msg(response, self.g_wxid, [], self.extra)

    def vp_sky_jl(self, content):
        """sky季蜡"""
        file = self.service.get_sky_file('jl')
        fp = file.get('save_path')
        if fp:
            fp = Dir.wechat_dir(f'{fp}')
            self.extra.update({"file": file})
            return self.client.send_img_msg(fp, self.g_wxid, self.extra)
        response = '暂未查询到季蜡'
        return self.client.send_msg(response, self.g_wxid, [], self.extra)

    def vp_sky_mf(self, content):
        """sky魔法"""
        file = self.service.get_sky_file('mf')
        fp = file.get('save_path')
        if fp:
            fp = Dir.wechat_dir(f'{fp}')
            self.extra.update({"file": file})
            return self.client.send_img_msg(fp, self.g_wxid, self.extra)
        response = '暂未查询到魔法'
        return self.client.send_msg(response, self.g_wxid, [], self.extra)

    def vp_sky_dl(self, content):
        """sky大蜡"""
        file = self.service.get_sky_file('dl')
        fp = file.get('save_path')
        if fp:
            fp = Dir.wechat_dir(f'{fp}')
            self.extra.update({"file": file})
            return self.client.send_img_msg(fp, self.g_wxid, self.extra)
        response = '暂未查询到大蜡'
        return self.client.send_msg(response, self.g_wxid, [], self.extra)

    def vp_sky_permanent(self, content):
        """sky常驻文件"""
        code = str(content).replace('#', '').strip()
        p_list = {"神龛": "sk", "献祭": "xj", "烛火": "zh"}
        f_type = p_list.get(code, '')
        if not f_type:
            return False
        file = self.service.get_sky_file(f_type)
        fp = file.get('save_path')
        if fp:
            fp = Dir.wechat_dir(f'{fp}')
            self.extra.update({"file": file})
            return self.client.send_img_msg(fp, self.g_wxid, self.extra)
        return False

    def vp_zxz_tq(self, content):
        """zxz天气"""
        city = str(content).replace('#天气', '').strip()
        if len(city) < 2:
            response = '请输入"#天气 [城市]"进行查询，如： #天气 上海'
        else:
            s_res = self.service.get_weather(city)
            response = s_res.get('main', "暂未查询到天气")
        return self.client.send_msg(response, self.g_wxid, [], self.extra)

    def vp_zxz_v50(self, content):
        """zxzV50"""
        s_res = self.service.get_v50()
        response = s_res.get('main', "暂未查询到v50")
        return self.client.send_msg(response, self.g_wxid, [], self.extra)

    def vp_ov_wa(self, content):
        """ov文案"""
        s_res = self.service.get_wa()
        response = s_res.get('main', "暂未查询到文案")
        return self.client.send_msg(response, self.g_wxid, [], self.extra)

    def vp_ov_bz(self, content):
        """ov壁纸"""
        r_num = random.randint(1, 999)
        file = self.service.get_sky_file('bz', {"r_num": r_num})
        fp = file.get('save_path')
        if fp:
            fp = Dir.wechat_dir(f'{fp}')
            self.extra.update({"file": file})
            return self.client.send_img_msg(fp, self.g_wxid, self.extra)
        response = '暂未查询到壁纸'
        return self.client.send_msg(response, self.g_wxid, [], self.extra)

    def vp_th(self, content=''):
        """历史上的今天"""
        s_res = self.service.get_today_history()
        response = s_res.get('main', "暂未查询到历史上的今天")
        return self.client.send_msg(response, self.g_wxid, [], self.extra)

    def vp_xw(self, content=''):
        """每日新闻"""
        self.vp_ov_wa('')
        Sys.delayed_task(lambda: self.vp_th(''), delay_seconds=15)
        file = self.service.get_sky_file('xw')
        fp = file.get('save_path')
        if fp:
            fp = Dir.wechat_dir(f'{fp}')
            self.extra.update({"file": file})
            return self.client.send_img_msg(fp, self.g_wxid, self.extra)
        response = '暂未查询每日新闻'
        return self.client.send_msg(response, self.g_wxid, [], self.extra)

    def vp_ov_cg(self, content):
        """ov唱歌"""
        r_num = random.randint(1, 61)
        file = self.service.get_sky_file('ng', {"r_num": r_num})
        fp = file.get('save_path')
        if fp:
            fp = Dir.wechat_dir(f'{fp}')
            self.extra.update({"file": file})
            return self.client.send_voice_message(fp, self.g_wxid, self.extra)
        response = '歌曲已失效'
        return self.client.send_msg(response, self.g_wxid, [], self.extra)

    def vp_dg(self, content):
        """点歌"""
        s_type = 'qq'
        code = str(content).replace('#点歌', '').strip()
        if '#' in code:
            code, t = code.rsplit('#', 1)
            if str(t).lower() in ['qq', 'wy']:
                s_type = t
        res = MusicSearchClient(s_type).get_song_data(code)
        if res:
            return self.client.send_dg_message(res, self.g_wxid, self.extra)
        response = '暂未找到该歌曲'
        return self.client.send_msg(response, self.g_wxid, [], self.extra)

    def vp_setting(self, content):
        """设置"""
        response = '设置功能正在开发中……'
        return self.client.send_msg(response, self.g_wxid, [], self.extra)

    def vp_report(self, content):
        """总结"""
        is_force = 0
        s_g_wxid = self.g_wxid
        code = str(content).replace('#总结', '').strip()
        if self.g_wxid != self.a_g_wxid:
            if '' != code:
                return False
        else:
            if '' == code:
                return False
            if 3 != len(code) or not code.isdigit() or '0' not in code:
                return False
            gid, is_force = map(int, code.split('0', 1))
            rdb = 'model.wechat.wechat_room_model.WechatRoomModel.get_info'
            room = Transfer.middle_exec(rdb, [], gid)
            if not room:
                return False
            s_g_wxid = self.a_g_wxid
            self.g_wxid = room['g_wxid']
            self.g_wxid_name = room['nickname']
            self.extra.update({
                "g_wxid": self.g_wxid,
                "g_wxid_name": self.g_wxid_name
            })
        # response = '数据收集中...\r\n\r\n正在进行总结，请稍后……'
        # self.client.send_msg(response, self.g_wxid, [], self.extra)
        fn_img = AIReportGenService.get_report_img(self.extra, 'simple', is_force)
        if fn_img:
            self.extra.update({"fn_img": fn_img})
            return self.client.send_img_msg(fn_img, s_g_wxid, self.extra)
        return False

    def vp_normal_msg(self, response, ats=None, extra=None):
        """发送普通群消息"""
        ats = ats if ats else []
        extra = extra if extra else self.extra
        return self.client.send_msg(response, self.g_wxid, ats, extra)

    def vp_card_msg(self, title, des, url='#', head='', extra=None):
        """发送卡片群消息"""
        extra = extra if extra else self.extra
        res = {
            "title": title,
            "des": str(des).replace('%s_wxid_name%', self.s_wxid_name),
            "url": url,
            "thumb": head if head else self.g_wxid_head,
        }
        return self.client.send_card_message(res, self.g_wxid, extra)
