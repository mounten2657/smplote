import os
from pathlib import Path
from utils.grpc.vpp_serve.vpp_serve_client import VppServeClient
from tool.core import File, Time, Logger

logger = Logger()


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
    def download_website_file(url, biz_code, file_name, file_dir='', fty=5002):
        """
        下载外部网站文件 - 对外方法
        :param str url: 文件url
        :param str biz_code: 业务码
        :param str file_name: 文件名 - 无路径 - 带后缀
        :param str file_dir: 文件路径 - 默认月份 - / 结尾
        :param int fty: 文件下载方式: 5001: http | 5002: curl  # 因为 5002 可以忽略证书验证，所以将其设为默认值
        :return: 可访问的文件链接 、文件md5 以及 文件大小
        {'url': ''xxx, 'md5': ''xxx, 'size': 100, 'code': 0, 'msg': "", 'save_path': 'xxx', 'file_name': 'xxx', 'fake_path': 'xxx', 'biz_code': 'xxx'}
        """
        key = biz_code.upper()
        if file_dir.startswith('/'):
            fp = f"/website{file_dir}{file_name}"
        else:
            file_dir = file_dir if file_dir else f"{Time.date('%Y%m')}/"
            fp = f"/website/{biz_code.lower().replace('vp_', '')}/{file_dir}{file_name}"
        fk = File.enc_dir(fp)
        logger.info(f'下载文件参数 - {(fty, key, url, fp, fk, 0)}', 'FILE_DOW_STA')
        res = VppServeClient().vp_download_file(fty, key, url, fp, fk, 0)
        logger.info(f'下载文件结果 - {res}', 'FILE_DOW_END')
        data = res.get('data', {})
        data.update({
            "save_path": fp,
            "file_name": os.path.basename(fp),
            "fake_path": fk,
            "biz_code": biz_code,
        })
        return data

    @staticmethod
    def mp3_to_silk(mp3_path: str):
        """将 mp3 转为 silk"""
        try:
            pcm_path = Path(mp3_path).with_suffix('.pcm')
            silk_path = Path(mp3_path).with_suffix('.silk')
            if not os.path.exists(pcm_path):
                if 0 != os.system(f'/usr/bin/ffmpeg -y -i {mp3_path} -f s16le -ar 24000 -ac 1 {pcm_path}'):
                    return ''
            if 0 == os.system(f'/opt/shell/tool/silk-v3-decoder/silk/encoder {pcm_path} {silk_path} -tencent'):
                return silk_path
            return ''
        except Exception as e:
            raise RuntimeError(f"转silk文件失败: {str(e)}")

