from service.vpp.vpp_serve_service import VppServeService
from model.biz.biz_file_model import BizFileModel


class BizFileService:

    def __init__(self):
        self.client = VppServeService()

    def get_biz_file(self, fn, url, fd, biz_code, sub_type):
        """
        获取原文件 - 自动下载
        :param fn:  文件名（带后缀）
        :param url:  文件网络地址
        :param fd:  文件二级目录（无特殊留空）
        :param biz_code:  业务代码
        :param sub_type:  子类别
        :return:  文件入库后的信息
        """
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

