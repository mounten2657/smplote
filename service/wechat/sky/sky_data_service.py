import random
from service.vpp.vpp_serve_service import VppServeService
from model.wechat.wechat_file_model import WechatFileModel
from tool.core import Time, Http, Env, Ins


class SkyDataService:

    _ZXZ_API = 'https://api.zxz.ee'
    _OVO_API = 'https://ovoav.com'
    _OVO_API_FILE_LIST = {
        "rw": "/api/sky/rwtp/rwt",
        "hs": "/api/skygm/hs",
        "rl": "/api/sky/rltp/rl",
        "mf": "/api/sky/mftp/mf",
        "jl": "/api/sky/jlwz/jl",
        "dl": "/api/sky/dlzwz/dl",
        "xz": "/api/skygm/gfxz",
        "db": "/api/sky/hbtp/hb",
        "bz": "/api/dmtp/dm/dm",
    }

    def __init__(self):
        self.client = VppServeService()
        self.ovo_key = Env.get('AI_API_KEY_WEB_GPT')
        self.api_type = 'ovo'

    def get_sky_file(self, sky_type='rw', extra=None):
        """
        获取sky任务文件
        :param sky_type:  rw | hs | jl | mf | yj | rl | dl | xz | db | bz | ng
        :param extra:  额外参数
        :return:  文件入库后的信息
        """
        fn, url = self._get_sky_filename(sky_type, extra)
        fdb = WechatFileModel()
        file = fdb.get_biz_file_info('VP_SKY', sky_type, fn)
        if not file:
            self.down_sky_file(sky_type, extra)
        file = fdb.get_biz_file_info('VP_SKY', sky_type, fn)
        return file

    def down_sky_file(self, sky_type='rw', extra=None):
        """
        下载sky任务文件
        :param sky_type:  rw | hs | jl | mf | yj | rl | dl | xz | db | bz | ng
        :param extra:  额外参数
        :return:  文件ID
        """
        fn, url = self._get_sky_filename(sky_type, extra)
        if not fn or not url:
            return {}
        file = self.client.download_website_file(url, 'VP_SKY', fn)
        fid = 0
        if file.get('url'):
            fdb = WechatFileModel()
            f_info = fdb.get_file_info(file['md5'])
            if f_info:
                fid = f_info['id']
            else:
                fid = fdb.add_file(file, {
                    "send_wxid": sky_type,
                    "send_wxid_name": fn,
                    "pid": 0,
                    "msg_id": 0,
                    "to_wxid": '',
                    "to_wxid_name": '',
                    "g_wxid": Time.date('%Y%m%d'),
                    "g_wxid_name": self.api_type,
            })
        return fid

    def _get_sky_filename(self, sky_type, extra):
        """获取sky文件名称"""
        extra = extra if extra else {}
        if 'yj' == sky_type:
            r_num = extra.get('r_num') if extra.get('r_num') else random.randint(1, 24)
            fn = f"sky_{sky_type}_{r_num}.mp3"
            url = f"{self._ZXZ_API}/api/sjyjsj/m/{r_num}.mp3"
        elif 'ng' == sky_type:
            r_num = extra.get('r_num') if extra.get('r_num') else random.randint(1, 199)
            fn = f"sky_{sky_type}_{r_num}.mp3"
            url = f"{self._OVO_API}/api/muic/nscg/nscg/{r_num}.mp3"
        else:
            api = self._OVO_API_FILE_LIST[sky_type]
            fn = f"sky_{sky_type}_{Time.date('%Y%m%d')}.png"
            url = f"{self._OVO_API}{api}?key={self.ovo_key}"
        return fn, url

    def get_sky_gg(self):
        """
        获取sky公告
        :return: {"title": "xxx", "main": "xxx"}
        """
        url = f"{self._ZXZ_API}/api/sky-gg/"
        data = Http.send_request('GET', url)
        if data.get('main'):
            text = "【Sky最新公告】\r\n"
            text += f"\r\n## {data['title']}\r\n"
            text += f"\r\n>{data['main']}\r\n"
            data['main'] = text
        return data

    def get_sky_sg(self, code):
        """
        获取sky身高 - 一码一测
        :param code: 好友码
        :return: {"title": "xxx", "main": "xxx"}
        """
        url = f"{self._OVO_API}/api/sky/sgwz/sgd?key={self.ovo_key}&id={code}"
        res = Http.send_request('GET', url)
        text = res
        return {"title": "身高测量", "main": text}

    # @Ins.cached('SKY_OVO_DJS')
    def get_sky_djs(self):
        """
        获取sky倒计时
        :return: {"title": "xxx", "main": "xxx"}
        """
        url = f"{self._OVO_API}/api/skygm/hd?key={self.ovo_key}"
        res = Http.send_request('GET', url)
        text = res.get('hb', '')
        if text:
            ts = text.split('国际服', 1)
            text = ts[0]
        url = f"{self._OVO_API}/api/sky/jjsj/sj?key={self.ovo_key}"
        res = Http.send_request('GET', url)
        text += "\r\n季节季蜡：\r\n"
        for i in range(1, 10):
            text += f"{res.get(f'msg{i}', '')}\r\n"
        url = f"{self._OVO_API}/api/sky/gymf/mf?key={self.ovo_key}"
        res = Http.send_request('GET', url)
        text += "\r\n魔法家具：\r\n" + res.get('dadmf', '')
        return {"title": "倒计时", "main": text, "code": 0}

    def get_v50(self):
        """
        获取v50文案
        :return: {"title": "xxx", "main": "xxx"}
        """
        url = f"{self._ZXZ_API}/api/v50/"
        text = Http.send_request('GET', url)
        return {"title": "v50", "main": text}

    def get_weather(self, city):
        """
        获取天气 - 今明后
        {
            "code": 200,
            "msg": "查询成功",
            "city": "中国江苏省南通市通州区",
            "data": [
                {
                    "date": "今天",
                    "weather": "小雨",
                    "temperature": "15° / 21°",
                    "wind": "北风",
                    "wind_level": "1级",
                    "air_quality": "31 优"
                }
            ]
         }
        :return: {"title": "xxx", "main": "xxx"}
        """
        url = f"{self._ZXZ_API}/api/weather/?city={city}"
        res = Http.send_request('GET', url)
        if res.get('data'):
            data_list = res.get('data')
            text = f"【天气预报】\r\n{res.get('city')}\r\n"
            for data in data_list:
                text += f"\r\n## {data['date']}: "
                text += f"\r\n天气：{data['weather']} {data['temperature']}"
                text += f"\r\n风力：{data['wind']} {data['wind_level']}"
                text += f"\r\n空气：{data['air_quality']}\r\n"
            return {"title": res.get('city'), "main": text, "data_list": data_list}
        return {"title": city, "main": f"暂未查询到{city}天气"}

    def get_wa(self):
        """
        获取随机文案
        :return: {"title": "xxx", "main": "xxx"}
        """
        url = f"{self._OVO_API}/api/wa/sjyy/yyan?key={self.ovo_key}"
        res = Http.send_request('GET', url)
        text = res.get('data', '')
        return {"title": "随机文案", "main": text}
