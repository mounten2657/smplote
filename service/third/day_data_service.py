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
        获取实时新闻 - 文字版
        :return: 接口结果
        """
        url1 = f"https://news.orz.ai/api/v1/dailynews/?platform=douyin"
        url2 = f"https://news.orz.ai/api/v1/dailynews/?platform=eastmoney"
        res = Http.send_request('GET', url1)
        r1 = res.get('data') if isinstance(res, dict) else res
        Time.sleep(1)
        res = Http.send_request('GET', url2)
        r2 = res.get('data') if isinstance(res, dict) else res
        text = f"{Time.date('%Y%m%d')} 实时热点速览\r\n"
        for i in range(10):
            if Attr.get(r1, i):
                text += f" - {Attr.get(r1[i], 'title')}\r\n"
            if Attr.get(r2, i):
                text += f" - {Attr.get(r2[i], 'title')}\r\n"
        return text.strip()

    def get_random_text(self):
        """
        获取随机文案 - 用于测试网络和连通性
        :return: 接口结果
        """
        url = f"https://uapis.cn/api/v1/saying"
        res = Http.send_request('GET', url)
        text = res.get('text', str(res))
        return text



