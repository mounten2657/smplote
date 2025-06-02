import os
from utils.grpc.vpp_serve.vpp_serve_client import VppServeClient
from tool.core import File, Time


class VppServeService:

    @staticmethod
    def download_file(fty, key, url, fp, fk, fd=0):
        """
        下载文件 - 对外方法
        :param int fty: 文件类型
        :param str key: 加密密钥
        :param str url: 加密url
        :param str fp: 文件保存路径
        :param str fk: 假名 - 需唯一
        :param int fd: 是否强制下载,，默认否
        :return: 可访问的文件链接 、文件md5 以及 文件大小
        """
        return VppServeClient().vp_download_file(fty, key, url, fp, fk, fd)

    @staticmethod
    def download_website_file(url, biz_code, file_name):
        """
        下载外部网站文件 - 对外方法
        :param str url: 文件url
        :param str biz_code: 业务码
        :param str file_name: 文件名 - 无路径 - 带后缀
        :return: 可访问的文件链接 、文件md5 以及 文件大小
        """
        fty = 5001
        key = biz_code.upper()
        fp = f"/website/{biz_code.lower().replace('vp_', '')}/{Time.date('%Y%m')}/{file_name}"
        fk = File.enc_dir(fp)
        res = VppServeClient().vp_download_file(fty, key, url, fp, fk, 0)
        data = res.get('data', {})
        data.update({
            "save_path": fp,
            "file_name": os.path.basename(fp),
            "fake_path": fk,
            "biz_code": biz_code,
        })
        return data
