import random
from service.vpp.vpp_serve_service import VppServeService
from model.wechat.wechat_file_model import WechatFileModel
from tool.core import Time, Http


class SkyDataService:

    _ZXZ_API = 'https://api.zxz.ee'

    def __init__(self):
        self.client = VppServeService()

    def get_sky_file(self, sky_type='rw', extra=None):
        """
        获取sky任务文件
        :param sky_type:  rw | hs | jl | mf | yj
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
        :param sky_type:  rw | hs | jl | mf | yj
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
                    "g_wxid_name": 'zxz',
            })
        return fid

    def _get_sky_filename(self, sky_type, extra):
        """获取sky文件名称"""
        extra = extra if extra else {}
        if sky_type in ['rw', 'hs', 'jl', 'mf']:
            fn = f"sky_{sky_type}_{Time.date('%Y%m%d')}.png"
            url = f"{self._ZXZ_API}/api/sky/?type=&lx={sky_type}"
        elif 'yj' == sky_type:
            r_num = extra.get('r_num') if extra.get('r_num') else random.randint(1, 24)
            fn = f"sky_{sky_type}_{r_num}.mp3"
            url = f"{self._ZXZ_API}/api/sjyjsj/m/{r_num}.mp3"
        else:
            return '', ''
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
                text += f"\r\n{data['date']}: "
                text += f"\r\n{data['weather']} {data['temperature']}"
                text += f"\r\n{data['wind']} {data['wind_level']}"
                text += f"\r\n{data['air_quality']}\r\n"
            return {"title": res.get('city'), "main": text, "data_list": data_list}
        return {"title": city, "main": f"暂未查询到{city}天气"}
