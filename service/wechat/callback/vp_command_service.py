import time
import random
from service.ai.command.ai_command_service import AiCommandService
from service.sky.sky_data_service import SkyDataService
from service.ai.report.ai_report_gen_service import AIReportGenService
from tool.unit.song.music_search_client import MusicSearchClient
from tool.db.cache.redis_client import RedisClient
from utils.wechat.qywechat.qy_client import QyClient
from utils.wechat.vpwechat.vp_client import VpClient
from tool.core import Config, Attr, Sys, Dir, Transfer, Time, Str


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
    #日榜 - 群聊天记录排名统计

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
            def self_voice_msg(f, g, e):
                return self.client.send_voice_message(f, g, e)
            Sys.delayed_task(self_voice_msg, fp, self.g_wxid, self.extra, delay_seconds=15)
        return self.client.send_msg(response, self.g_wxid, self.at_list, self.extra)

    def vp_sky_rw(self, content='', is_all=0):
        """sky任务"""
        content = '#任务' if '201' == content else content
        code = str(content).replace('#任务', '').strip()
        if 1 == len(code) and int(code) > 0:
            is_all = int(code)
        # 新增文字版 - 都熟悉了，没必要图片，占内存
        if 2 == is_all:
            s_res = self.service.get_rw_txt()
            response = s_res.get('main', "暂未查询到每日任务")
            return self.client.send_msg(response, self.g_wxid, [], self.extra)
        # 以下是之前的正常逻辑
        file = self.service.get_sky_file('rw')
        fp = file.get('save_path')
        if fp:
            fp = Dir.wechat_dir(f'{fp}')
            self.extra.update({"file": file})
            self.client.send_img_msg(fp, self.g_wxid, self.extra)
            # 其它相关信息也一并发送
            if is_all:
                jl = self.service.get_sky_file('jl')
                self.extra.update({"file": jl})
                jl.get('save_path') and self.client.send_img_msg(Dir.wechat_dir(f'{jl['save_path']}'), self.g_wxid, self.extra)
                dl = self.service.get_sky_file('dl')
                self.extra.update({"file": dl})
                dl.get('save_path') and self.client.send_img_msg(Dir.wechat_dir(f'{dl['save_path']}'), self.g_wxid, self.extra)
                mf = self.service.get_sky_file('mf')
                self.extra.update({"file": mf})
                mf.get('save_path') and self.client.send_img_msg(Dir.wechat_dir(f'{mf['save_path']}'), self.g_wxid, self.extra)
            return True
        response = '获取sky任务失败'
        return self.client.send_msg(response, self.g_wxid, self.at_list, self.extra)

    def vp_sky_hs(self, content='', is_all=0):
        """sky红石"""
        content = '#红石' if '202' == content else content
        code = str(content).replace('#红石', '').strip()
        if 1 == len(code) and int(code) > 0:
            is_all = int(code)
        # 新增文字版，节省空间
        is_week = Time.week() < 5
        if 2 == is_all:
            if is_week:
                return False
            s_res = self.service.get_hs_txt()
            response = s_res.get('main', '')
            return self.client.send_msg(response, self.g_wxid, [], self.extra) if response else False
        if is_all and is_week:
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

    def vp_sky_rl(self, content, is_all=0):
        """sky日历"""
        code = str(content).replace('#日历', '').strip()
        if 1 == len(code) and int(code) > 0:
            is_all = int(code)
        if 2 == is_all:
            # 只发送文字版
            text = self.service.get_sky_djs()
            return self.client.send_msg(text['main'], self.g_wxid, [], self.extra)
        file = self.service.get_sky_file('rl')
        fp = file.get('save_path')
        if fp:
            fp = Dir.wechat_dir(f'{fp}')
            self.extra.update({"file": file})
            self.client.send_img_msg(fp, self.g_wxid, self.extra)
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

    def vp_ov_wa(self, content=''):
        """ov文案"""
        s_res = self.service.get_wa()
        response = s_res.get('main', "暂未查询到文案")
        return self.client.send_msg(response, self.g_wxid, [], self.extra)

    def vp_ov_bz(self, content):
        """ov壁纸"""
        r_num = 0
        # 壁纸失败率太高，如果没有成功，重试两次
        for i in range(5):
            r_num = random.randint(1, 999)
            file = self.service.get_sky_file('bz', {"r_num": r_num})
            fp = file.get('save_path')
            if fp:
                fp = Dir.wechat_dir(f'{fp}')
                self.extra.update({"file": file})
                return self.client.send_img_msg(fp, self.g_wxid, self.extra)
            Time.sleep(1)
        response = f'暂未查询到壁纸 - [{r_num}]'
        return self.client.send_msg(response, self.g_wxid, [], self.extra)

    def vp_th(self, content=''):
        """历史上的今天"""
        s_res = self.service.get_today_history()
        response = s_res.get('main', "暂未查询到历史上的今天")
        return self.client.send_msg(response, self.g_wxid, [], self.extra)

    def vp_xw(self, content=''):
        """每日新闻 - 文字版"""
        s_res = self.service.get_daily_news()
        response = s_res.get('main', "暂未查询到每日新闻")
        tl = response.split('\n-')
        if len(tl) > 1:
            n = int(len(tl) / 2) + 1
            response = "\r\n".join(tl[:n])
        self.client.send_msg(response, self.g_wxid, [], self.extra)
        return self.vp_th()

    def vp_xw_img(self, content=''):
        """每日新闻 - 图片版"""
        file = self.service.get_sky_file('xw')
        fp = file.get('save_path')
        if fp:
            fp = Dir.wechat_dir(f'{fp}')
            self.extra.update({"file": file})
            self.client.send_img_msg(fp, self.g_wxid, self.extra)
            return self.vp_th()
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
        s_type = 'WY' if '网易' in content else 'QQ'
        code = Str.replace_multiple(content, ['#', '点歌', '网易'], ['', '', ''])
        res = MusicSearchClient(s_type).get_song_data(code.strip())
        if res:
            return self.client.send_dg_message(res, self.g_wxid, self.extra)
        response = '暂未找到该歌曲'
        return self.client.send_msg(response, self.g_wxid, [], self.extra)

    def vp_setting(self, content):
        """设置"""
        response = '设置功能正在开发中……'
        return self.client.send_msg(response, self.g_wxid, [], self.extra)

    def vp_report(self, content):
        """聊天总结"""
        code = str(content).replace('#总结', '').strip()
        check, s_g_wxid, is_force = self._check_g_wxid(code)
        if not check:
            return False
        fn_img = AIReportGenService.get_report_img(self.extra, 'simple', is_force)
        if fn_img:
            self.extra.update({"fn_img": fn_img})
            return self.client.send_img_msg(fn_img, s_g_wxid, self.extra)
        return False

    def vp_rank(self, content):
        """聊天排名"""
        rs_list = {1: '#昨日榜', 0: '#日榜', 30: '#月榜', 90: '#季榜', 180: '#半年榜', 365: '#年榜'}
        rt = rn = None
        for i, rs in rs_list.items():
            if rs in content:
                rt = i
                rn = rs
                break
        if rt is None:
            return False
        code = Str.replace_multiple(content, rs_list.values()).strip()
        check, s_g_wxid, is_force = self._check_g_wxid(code)
        if not check:
            return False
        m_date_list = ['', '']
        if rt != 1:
            m_date_list[0] = Time.dft(Time.now() - rt * 86400, "%Y-%m-%d 00:00:00")
            m_date_list[1] = Time.dft(Time.now(), "%Y-%m-%d 23:59:59")
        rdb = 'model.wechat.wechat_msg_model.WechatMsgModel.get_msg_times_rank'
        r_list, r_count = Transfer.middle_exec(rdb, [], self.g_wxid, m_date_list)
        if r_list:
            response = f"【{r_list[0]['g_wxid_name']}】#群聊榜单 {rn}"
            for r in r_list:
                percent = round(100 * r['count'] / r_count, 3)
                percent = f"T{Str.rev_float(percent, 3, 2)}{Str.randint(1, 9)}"
                response += f"\r\n  - {r['s_wxid_name']} {r['count']}次 <{percent}>"
            return self.client.send_msg(response, s_g_wxid, [], self.extra)
        return False

    def _check_g_wxid(self, code):
        """检查群指令是否正确"""
        is_force = 0
        s_g_wxid = self.g_wxid
        if self.g_wxid != self.a_g_wxid:
            if '' != code:
                return False, '', 0
        else:
            if '' == code:
                return False, '', 0
            if 3 != len(code) or not code.isdigit() or '0' not in code:
                return False, '', 0
            gid, is_force = map(int, code.split('0', 1))
            rdb = 'model.wechat.wechat_room_model.WechatRoomModel.get_info'
            room = Transfer.middle_exec(rdb, [], gid)
            if not room:
                return False, '', 0
            # 除了管理员群，其他群自己看自己群的信息
            if self.g_wxid != self.a_g_wxid and room['g_wxid'] != self.g_wxid:
                return False, '', 0
            s_g_wxid = self.a_g_wxid
            self.g_wxid = room['g_wxid']
            self.g_wxid_name = room['nickname']
            self.extra.update({
                "r_wxid": s_g_wxid,
                "g_wxid": self.g_wxid,
                "g_wxid_name": self.g_wxid_name
            })
        return True, s_g_wxid, is_force

    def vp_morning(self, content=''):
        """早安问候语"""
        m_list = [
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
        response = Attr.random_choice(m_list)
        return self.client.send_msg(response, self.g_wxid, [], self.extra)

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
