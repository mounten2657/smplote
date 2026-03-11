import time
import random
from service.sky.sky_data_service import SkyDataService
from service.wechat.reply.vp_msg_service import VpMsgService
from service.ai.command.ai_command_service import AiCommandService
from service.ai.report.ai_report_gen_service import AIReportGenService
from service.vpp.vpp_clash_service import VppClashService
from tool.unit.song.music_search_client import MusicSearchClient
from tool.db.cache.redis_client import RedisClient
from utils.wechat.qywechat.qy_client import QyClient
from utils.wechat.vpwechat.vp_client import VpClient
from tool.core import Config, Attr, Sys, Dir, Transfer, Time, Str

redis = RedisClient()


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
        user = Attr.select_item_by_where(room.get('member_list', []), {"wxid": self.self_wxid}, {})
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
    #身高查询 - 身高预测计算
    #光翼查询 - 光翼散落统计
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
    #流量 - 节点流量统计
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
        """is_all:  0: 仅任务图片 | 1: 所有任务相关图片 | 2: 文字版 | 20: 图片+文字 | 21: 所有图片+文字"""
        content = '#任务' if '201' == content else content
        code = str(content).replace('#任务', '').strip()
        if len(code) <= 2 and int(code if code else 0) > 0:
            is_all = int(code)
        # 新增文字版 - 都熟悉了，没必要图片，占内存
        if 2 == is_all:
            return self.vp_sky_rw_txt()
        # 以下是之前的正常逻辑
        file = self.service.get_sky_file('rw')
        fp = file.get('save_path')
        if fp:
            fp = Dir.wechat_dir(f'{fp}')
            self.extra.update({"file": file})
            self.client.send_img_msg(fp, self.g_wxid, self.extra)
            if is_all in [1, 21]:
                # 其它相关信息也一并发送
                jl = self.service.get_sky_file('jl')
                self.extra.update({"file": jl})
                jl.get('save_path') and self.client.send_img_msg(Dir.wechat_dir(f'{jl['save_path']}'), self.g_wxid, self.extra)
                # 大蜡和魔法不常用，先屏蔽
                # dl = self.service.get_sky_file('dl')
                # self.extra.update({"file": dl})
                # dl.get('save_path') and self.client.send_img_msg(Dir.wechat_dir(f'{dl['save_path']}'), self.g_wxid, self.extra)
                # mf = self.service.get_sky_file('mf')
                # self.extra.update({"file": mf})
                # mf.get('save_path') and self.client.send_img_msg(Dir.wechat_dir(f'{mf['save_path']}'), self.g_wxid, self.extra)
        if is_all == 20:
            return self.vp_sky_rw_txt()
        # 没有查询到
        return False

    def vp_sky_rw_txt(self, content=''):
        """sky任务 - 文字版"""
        s_res = self.service.get_rw_txt()
        response = s_res.get('main', "暂未查询到每日任务")
        return self.client.send_msg(response, self.g_wxid, [], self.extra)

    def vp_sky_hs(self, content='', is_all=2):
        """sky红石"""
        """is_all:  0: 图片(每天发) | 1: 图片(仅周末发) | 2: 文字版(仅周末发)"""
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
        """sky身高查询"""
        cache_key = 'LOCK_SKY_API_SG'
        if redis.get(cache_key, [self.s_wxid]) and not self.is_admin:
            return self.client.send_msg('每分钟只能查询身高一次', self.g_wxid, self.at_list, self.extra)
        content = '#身高查询' if '203' == content else content
        code = str(content).replace('#身高查询', '').strip()
        if len(code) < 14:
            response = '请输入"#身高查询 [好友码]"进行查询(备注不能含敏感字)，如： #身高查询 B1A9-KMV2-4ZG5  (注：第一次好友码，后续长ID)'
        elif self.g_wxid_count > 50:
            # response = '只有管理员才能使用该功能'
            response = '哦No！欠费了，谁赞助一下，一毛一次'
        else:
            s_res = self.service.get_sky_sg(code)
            response = s_res.get('main', "暂未查询到身高")
        return self.client.send_msg(response, self.g_wxid, self.at_list, self.extra)

    def vp_sky_gy(self, content):
        """sky光翼查询"""
        cache_key = 'LOCK_SKY_API_GY'
        if redis.get(cache_key, [self.s_wxid]) and not self.is_admin:
            return self.client.send_msg('每分钟只能查询光翼一次', self.g_wxid, self.at_list, self.extra)
        content = '#光翼查询' if '204' == content else content
        code = str(content).replace('#光翼查询', '').strip()
        if len(code) < 9:
            response = '请输入"#光翼查询 [短ID]"进行查询，如： #光翼查询 908339761'
        else:
            s_res = self.service.get_sky_gy(code)
            response = s_res.get('main', "暂未查询到光翼")
        return self.client.send_msg(response, self.g_wxid, self.at_list, self.extra)

    def vp_sky_lb(self, content):
        """sky礼包查询"""
        cache_key = 'LOCK_SKY_API_GY'
        if redis.get(cache_key, [self.s_wxid]) and not self.is_admin:
            return self.client.send_msg('每分钟只能查询礼包一次', self.g_wxid, self.at_list, self.extra)
        content = '#礼包查询' if '205' == content else content
        code = str(content).replace('#礼包查询', '').strip()
        if len(code) < 9:
            response = '请输入"#礼包查询 [长ID]"进行查询，如： #礼包查询 fe4b932e-837d-4989-b07f-e1941bfa364c'
        else:
            s_res = self.service.get_sky_lb(code)
            response = s_res.get('main', "暂未查询到礼包")
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
        if is_all in [2, 21]:
            # 只发送文字版
            text = self.service.get_sky_djs(is_all)
            return self.client.send_msg(text['main'], self.g_wxid, [], self.extra)
        # 图片版好像失效了，请用上面的文字版
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

    def vp_ov_bz(self, content, r_type=0):
        """ov壁纸"""
        r_num = 0
        code = str(content).replace('#壁纸', '').strip()
        r_type = r_type if r_type else Str.int(code)  # # 壁纸类型：1:二次元 | 2:必应 | 3:cosplay
        # 壁纸失败率太高，如果没有成功，重试两次
        for i in range(5):
            r_num = random.randint(1, 999)
            file = self.service.get_sky_file('bz', {"r_num": r_num, "r_type": r_type})
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

    def vp_xw(self, content='', is_all=0):
        """每日新闻 - 文字版"""
        """is_all: 0: 仅新闻 | 1: 新闻 + 历史上的今天"""
        s_res = self.service.get_daily_news()
        response = s_res.get('main', "")
        if response:
            res = self.client.send_msg(response, self.g_wxid, [], self.extra)
            is_all and  self.vp_th()
            return res
        return False

    def vp_sub_stat(self, content=''):
        """vpn 流量统计"""
        s_res = VppClashService().get_traffic_stat()
        return self.client.send_msg(s_res, self.g_wxid, [], self.extra)

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
        try:
            res = MusicSearchClient(s_type).get_song_data(code.strip())
        except Exception as e:
            if s_type == 'QQ':  # qq音乐搜索失败再次尝试使用网易搜索
                res = MusicSearchClient('WY').get_song_data(code.strip())
            else:
                return f"{e}"
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
                percent = f"T{Str.rev_float(percent, 3, 2, '')}{Str.randint(1, 9)}"
                response += f"\r\n  - {r['s_wxid_name']} <{r['count']}次|{percent}>"
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

    def vp_good_morning(self, content=''):
        """早安问候语"""
        return VpMsgService.vp_morning(self.g_wxid, self.app_key)
