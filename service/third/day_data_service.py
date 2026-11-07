from service.vpp.vpp_serve_service import VppServeService
from model.biz.biz_file_model import BizFileModel
from tool.core import Time, Http, Attr, Str


class DayDataService:

    def __init__(self):
        self.client = VppServeService()

    def get_biz_file(self, biz_code, sub_type, extra=None):
        """
        获取原文件 - 自动下载
        :param biz_code:  业务代码
        :param sub_type:  子类别
        :param extra:  额外信息
        :return:  文件入库后的信息
        """
        fn, url, fd = self._get_biz_fileinfo(sub_type, extra)
        fdb = BizFileModel()
        file = fdb.get_biz_file_info(biz_code, sub_type, fn)
        if not file:
            file = self._down_biz_file(fn, url, fd, biz_code, sub_type)
        return file if file else {}

    def _down_biz_file(self, fn, url, fd, biz_code, sub_type):
        """
        下载原文件
        :param fn:  文件名（带后缀）
        :param url:  文件网络地址
        :param fd:  文件二级目录（无特殊留空）
        :param biz_code:  业务代码
        :param sub_type:  子类别
        :return:  文件信息
        """
        if not fn or not url:
            return {}
        file = self.client.download_website_file(url, 'VP_BIZ', fn, fd)
        f_info = {}
        if file.get('url'):
            fdb = BizFileModel()
            f_info = fdb.get_file_info(file['md5'])
            if not f_info:
                fdb.add_file(file, {
                    "biz_code": biz_code,
                    "sub_type": sub_type,
                    "origin_url": url[:1024]
                })
                f_info = fdb.get_file_info(file['md5'])
        return f_info

    def _get_biz_fileinfo(self, biz_code, sub_type, extra=None):
        """
        获取业务文件信息
        :param biz_code:  业务代码
        :param sub_type:  子类别
        :param extra:  额外信息
        :return: 文件名 + 文件链接 + 文件二级目录
        """
        fn = url = fd = ''
        extra = extra if extra else {}
        if 'VP_WP' == biz_code:  # 壁纸类
            if 'bing' == sub_type:  # bing 每日壁纸
                url = f"https://api.nxvav.cn/api/bing/?encode=json"
                res = Http.send_request('GET', url, headers=Http.get_ua_header())  # 返回的结构可能随时变更，注意变通
                # {"code":200,"message":"获取成功","data":{"title":"一座比城市更悠久的教堂","description":"阿尼遗址的圣格雷戈里教堂，卡尔斯省，土耳其","cover":"https://bing.com/th?id=OHR.AniTurkey_ZH-CN5838141955_1920x1080.jpg","cover_4k":"https://bing.com/th?id=OHR.AniTurkey_ZH-CN5838141955_UHD.jpg","copyright":"© Kenan Talas/Getty Images","update_date":"2025-12-29 09:58:54","update_date_at":1766973534}}
                url = Attr.get_by_point(res, 'data.cover_4k', '')  # 1k 用 cover  |  4k 用 cover_4k
                byn = Str.filter_target_chars(Attr.get_by_point(res, 'data.title', '') + '-' + Attr.get_by_point(res, 'data.description', ''))
                fn = f"{Time.date('%Y%m%d')}_bing_{byn}.{url.split('.')[-1] if '.' in url else 'png'}"
        return fn, url, fd

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



