import random
from service.vpp.vpp_serve_service import VppServeService
from model.wechat.wechat_file_model import WechatFileModel
from tool.core import Time, Http, Env, Attr


class SkyDataService:

    _ZXZ_API = 'https://api.zxz.ee'
    _OVO_API = 'https://ovoav.com'
    _OVO_API_FILE_LIST = {
        "rw": "/api/sky/rwby/rw",  # "/api/sky/rwtp/rwt",
        "hs": "/api/sky/hstp/hs",
        "rl": "/api/sky/rltp/rl",
        "mf": "/api/sky/mftp/mf",
        "jl": "/api/sky/rwby/jl",     # "/api/sky/jlwz/jl",
        "dl": "/api/sky/rwby/dl",  # "/api/sky/dlzwz/dl",
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
        fn, url, fd = self._get_sky_filename(sky_type, extra)
        fdb = WechatFileModel()
        file = fdb.get_biz_file_info('VP_SKY', sky_type, fn)
        if not file:
            file = self.down_sky_file(sky_type, extra)
        return file if file else {}

    def down_sky_file(self, sky_type='rw', extra=None):
        """
        下载sky任务文件
        :param sky_type:  rw | hs | jl | mf | yj | rl | dl | xz | db | bz | ng
        :param extra:  额外参数
        :return:  文件信息
        """
        fn, url, fd = self._get_sky_filename(sky_type, extra)
        if not fn or not url:
            return {}
        file = self.client.download_website_file(url, 'VP_SKY', fn, fd)
        f_info = {}
        if file.get('url'):
            fdb = WechatFileModel()
            f_info = fdb.get_file_info(file['md5'])
            if not f_info:
                fdb.add_file(file, {
                    "send_wxid": sky_type,
                    "send_wxid_name": fn,
                    "pid": 0,
                    "msg_id": 0,
                    "to_wxid": '',
                    "to_wxid_name": url[:128],  # 记录一下源链接
                    "g_wxid": Time.date('%Y%m%d'),
                    "g_wxid_name": self.api_type,
                })
                f_info = fdb.get_file_info(file['md5'])
        return f_info

    def _get_sky_filename(self, sky_type, extra):
        """获取sky文件名称"""
        fd = ''
        extra = extra if extra else {}
        if 'yj' == sky_type:
            r_num = extra.get('r_num', 24)
            fn = f"sky_{sky_type}_{r_num}.mp3"
            url = f"{self._ZXZ_API}/api/sjyjsj/m/{r_num}.mp3"
        elif 'bz' == sky_type:
            r_num = extra.get('r_num', 999)
            if 0 == r_num % 3:
                # 真人cos壁纸
                fn = f"sky_{sky_type}_{r_num}_{Time.date('%Y%m%d')}.png"
                url = f"{self._ZXZ_API}/api/mhycos/?type=5&num=1"
                res = Http.send_request('GET', url)
                if isinstance(res, dict) and Attr.get_by_point(res, 'data.0.images'):
                    img_list = Attr.get_by_point(res, 'data.0.images')
                    i_num = 0 # random.randint(0, len(img_list) - 1)
                    url = img_list[i_num]
                else:
                    url = ''
            elif 1 == r_num % 3:
                # 二次元壁纸 - 好像没用了
                fn = f"sky_{sky_type}_{r_num}_{Time.date('%Y%m%d')}.png"
                url = f"{self._ZXZ_API}/api/ecy/?type=json"
                res = Http.send_request('GET', url)
                url = res.get('url') if isinstance(res, dict) and res.get('url') else ''
            else:
                # bing 每日壁纸
                fn = f"sky_{sky_type}_by_{Time.date('%Y%m%d')}.png"
                url = f"https://api.nxvav.cn/api/bing/?encode=json"
                res = Http.send_request('GET', url)
                url = res.get('url') if isinstance(res, dict) and res.get('url') else ''
            # 用这个兜底吧
            if not url:
                # 动漫壁纸
                api = self._OVO_API_FILE_LIST[sky_type]
                fn = f"sky_{sky_type}_{r_num}_0_{Time.date('%Y%m%d')}.png"
                url = f"{self._OVO_API}{api}?key={self.ovo_key}"
        elif 'xw' == sky_type:
            # 每日新闻
            fn = f"sky_{sky_type}_xw_{Time.date('%Y%m%d')}.png"
            url = 'https://zj.v.api.aa1.cn/api/60s/'
        elif 'ng' == sky_type:
            # 已经全部下载了，就61首
            r_list = [236,235,230,229,226,224,216,212,210,209,208,205,204,202,199,194,193,192,191,186,182,
                      180,177,176,171,168,167,160,159,158,157,156,148,146,145,144,140,139,135,133,132,128,
                      127,125,124,123,122,121,119,117,116,115,114,111,108,103,101,100,190,130,175]
            r_num = extra.get('r_num', 61)
            r_num = r_list[int(r_num) - 1]
            fn = f"sky_{sky_type}_{r_num}.mp3"
            url = f"{self._OVO_API}/api/muic/nscg/nscg/{r_num}.mp3"
        elif sky_type in ['sk', 'xj', 'zh']:
            # 常驻文件
            fn = f"sky_{sky_type}.png"
            url = f"http://localhost/fp"
            fd = 'permanent/'
        else:
            api = self._OVO_API_FILE_LIST[sky_type]
            fn = f"sky_{sky_type}_{Time.date('%Y%m%d')}.png"
            url = f"{self._OVO_API}{api}?key={self.ovo_key}"
        return fn, url, fd

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

    def get_sky_djs(self):
        """
        获取sky倒计时
        :return: {"title": "xxx", "main": "xxx"}
        """
        url = f"{self._OVO_API}/api/skygm/hd?key={self.ovo_key}"
        res = Http.send_request('GET', url)
        text = res.get('hb', '')
        url = f"{self._OVO_API}/api/sky/jjsj/sj?key={self.ovo_key}"
        res = Http.send_request('GET', url)
        text += "\r\n\r\n季节季蜡：\r\n"
        for i in range(1, 10):
            text += f"{res.get(f'msg{i}', '')}\r\n"
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

    def get_daily_news(self):
        """
        获取每日新闻 - 文字版
        :return: {"title": "xxx", "main": "xxx"}
        """
        url = f"https://api.mhimg.cn/api/Daily_news"
        res = Http.send_request('GET', url)
        text = res  # 直接返回文字，不是 json 格式
        return {"title": "每日新闻", "main": "【莫简报】\r\n" + text}

    def get_today_history(self):
        """
        获取历史上的今天 - 文字版
        :return: {"title": "xxx", "main": "xxx"}
        """
        url = f"{self._ZXZ_API}/api/lsjt/?type=json"
        res = Http.send_request('GET', url)
        text = res.get('data', [])
        return {"title": "历史上的今天", "main": "【历史上的今天】\r\n - " + "\r\n - ".join(text[:5])}

