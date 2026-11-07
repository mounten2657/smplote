from service.biz.biz_file_service import BizFileService
from tool.core import Time, Http, Attr, Str


class DayDataService:

    def get_bing_image(self):
        """
        获取 bing 每日壁纸
        :return: 文件存储后的信息
        """
        url = f"https://api.nxvav.cn/api/bing/?encode=json"
        res = Http.send_request('GET', url, headers=Http.get_ua_header())  # 返回的结构可能随时变更，注意变通
        # {"code":200,"message":"获取成功","data":{"title":"一座比城市更悠久的教堂","description":"阿尼遗址的圣格雷戈里教堂，卡尔斯省，土耳其","cover":"https://bing.com/th?id=OHR.AniTurkey_ZH-CN5838141955_1920x1080.jpg","cover_4k":"https://bing.com/th?id=OHR.AniTurkey_ZH-CN5838141955_UHD.jpg","copyright":"© Kenan Talas/Getty Images","update_date":"2025-12-29 09:58:54","update_date_at":1766973534}}
        url = Attr.get_by_point(res, 'data.cover_4k', '')  # 1k 用 cover  |  4k 用 cover_4k
        byn = Str.filter_target_chars(Attr.get_by_point(res, 'data.title', '') + '-' + Attr.get_by_point(res, 'data.description', ''))
        fn = f"{Time.date('%Y%m%d')}_bing_{byn}.{url.split('.')[-1] if '.' in url else 'png'}"
        return BizFileService().get_biz_file(fn, url, '', 'VP_WP', 'bing')

    def get_daily_news(self):
        """
        获取每日新闻 - 文字版
        :return: 接口结果
        """
        url = f"https://60s.viki.moe/v2/60s?encoding=text"  # 把 encoding 去掉就是 json 格式
        u = Http.get_base_url() + f'/src/nat/vps'  # 用 vps 转发获取结果
        headers = Http.get_ua_header()
        res = Http.send_request_auth('GET', u, {"u": url}, headers)
        text = res.get('data') if isinstance(res, dict) else res  # 直接返回文字
        # 失败则本地再试一次
        if text.startswith('HTTP request failed'):
            Time.sleep(10)
            res = Http.send_request('GET', url, headers=headers)
            text = res.get('data') if isinstance(res, dict) else res
        return text



