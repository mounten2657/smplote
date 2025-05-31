from utils.grpc.vpp_serve.vpp_serve_client import VppServeClient


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
