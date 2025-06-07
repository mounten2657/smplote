from service.ai.command.ai_command_service import AiCommandService
from service.wechat.sky.sky_data_service import SkyDataService
from service.ai.report.ai_report_gen_service import AIReportGenService
from tool.db.cache.redis_client import RedisClient
from utils.wechat.qywechat.qy_client import QyClient
from utils.wechat.vpwechat.vp_client import VpClient
from tool.core import Config, Attr, Sys, Dir


class VpCommandService:

    def __init__(self, app_key, g_wxid='', s_wxid=''):
        self.app_key = app_key
        self.client = VpClient(self.app_key)
        self.config = Config.vp_config()
        self.app_config = self.config['app_list'][self.app_key]
        self.self_wxid = self.app_config['wxid']
        self.g_wxid = g_wxid if g_wxid else self.app_config['g_wxid']
        self.s_wxid = s_wxid if s_wxid else self.self_wxid
        room = self.client.get_room(self.g_wxid)
        user = Attr.select_item_by_where(room.get('member_list', []), {"wxid": self.s_wxid})
        self.s_wxid_name = user.get('display_name', '')
        self.g_wxid_name = room.get('nickname', '')
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
        response = '工号9527为您服务，提问请按101，百科请按102，任务请按201，红石请按202，身高请按203，其它请按103'
        return self.client.send_msg(response, self.g_wxid, self.at_list, self.extra)

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
        QyClient(self.app_key).send_msg(self.app_key, f'{self.s_wxid_name} 正在呼唤你，请尽快回复')
        response = '已发送至管理员……\r\n\r\n正在呼唤本人，请稍后……'
        file = self.service.get_sky_file('yj')
        fp = file.get('save_path')
        if fp:
            fp = Dir.wechat_dir(f'{fp}')
            self.extra.update({"file": file})
            Sys.delayed_task(15, lambda: self.client.send_voice_message(fp, self.g_wxid, self.extra))
        return self.client.send_msg(response, self.g_wxid, self.at_list, self.extra)

    def vp_sky_rw(self, content):
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

    @staticmethod
    def vp_sky_rw_task(app_key, g_wxid, s_wxid):
        """定时任务专用方法"""
        commander = VpCommandService(app_key, g_wxid, s_wxid)
        return commander.vp_sky_rw('201')

    def vp_sky_hs(self, content):
        """sky红石"""
        content = '#红石' if '202' == content else content
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
            response = '请输入"#身高 [好友码]"进行查询，如： #身高 xxxx-xxxx-xxxx'
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

    def vp_zxz_tq(self, content):
        """zxz天气"""
        city = str(content).replace('#天气', '').strip()
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
        file = self.service.get_sky_file('bz')
        fp = file.get('save_path')
        if fp:
            fp = Dir.wechat_dir(f'{fp}')
            self.extra.update({"file": file})
            return self.client.send_img_msg(fp, self.g_wxid, self.extra)
        response = '暂未查询到壁纸'
        return self.client.send_msg(response, self.g_wxid, [], self.extra)

    def vp_ov_cg(self, content):
        """ov唱歌"""
        response = '唱歌功能正在开发中……'
        return self.client.send_msg(response, self.g_wxid, [], self.extra)

    def vp_dg(self, content):
        """点歌"""
        response = '点歌功能正在开发中……'
        return self.client.send_msg(response, self.g_wxid, [], self.extra)

    def vp_setting(self, content):
        """设置"""
        response = '设置功能正在开发中……'
        return self.client.send_msg(response, self.g_wxid, [], self.extra)

    def vp_report(self, content):
        """总结"""
        is_force = 0
        code = str(content).replace('#总结', '').strip()
        if '1' == code:
            is_force = 1
        response = '数据收集中...\r\n\r\n正在进行总结，请稍后……'
        self.client.send_msg(response, self.g_wxid, [], self.extra)
        fn_img = AIReportGenService.get_report_img(self.extra, 'simple', is_force)
        if fn_img:
            self.extra.update({"fn_img": fn_img})
            return self.client.send_img_msg(fn_img, self.g_wxid, self.extra)
        return False

    def vp_normal_msg(self, response, ats=None, extra=None):
        """发送普通群消息"""
        ats = ats if ats else []
        extra = extra if extra else self.extra
        return self.client.send_msg(response, self.g_wxid, ats, extra)
