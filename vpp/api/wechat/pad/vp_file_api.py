import os
import json
import base64
import hashlib
import requests


class VpFileApi:

    def __init__(self):
        self.config = self._load_config()
        self.server_url = self.config.get('server_url')
        self.server_key = self.config.get('server_key')
        self.static_url = self.config.get('static_url')
        self.save_path = self.config.get('save_path')

    def _load_config(self):
        file_path = 'config/vp.json'
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
        return json.loads(content)

    def download_file(self, fty: int, key: str, url: str, fp: str, fk: str, fd: int = 0):
        """
        通过CDN下载文件
        :param int fty: 文件类型
        :param str key: 加密密钥
        :param str url: 加密url
        :param str fp: 文件保存路径
        :param str fk: 假名 - 需唯一
        :param int fd: 是否强制下载,，默认否
        :return: 可访问的文件链接 、文件md5 以及 文件大小
        """
        res = {"url": "", "md5": "", "size": 0}
        output_file = f"{self.save_path}{fp}"
        base_path, file_ext = str(output_file).rsplit('.', 1)
        try:
            if not os.path.exists(output_file) or fd:
                os.makedirs(os.path.dirname(output_file), exist_ok=True)
                if 3001 == fty:  # emoji
                    output_file = self.download_url_file(url, output_file)
                elif 5001 == fty:  # website file
                    output_file = self.download_url_file(url, output_file)
                elif 5002 == fty:  # website file - curl
                    output_file = self.download_url_file_curl(url, output_file)
                else:  # 图视文音
                    api = '/message/SendCdnDownload'
                    payload = {
                        "AesKey": key,
                        "FileType": fty,
                        "FileURL": url,
                    }
                    api = f"{self.server_url}{api}?key={self.server_key}"
                    resp = requests.post(api, json=payload).json()
                    resp = resp if resp else {}
                    file_size = int(resp.get('Data', {}).get('TotalSize', 0))
                    file_data = resp.get('Data', {}).get('FileData', '')
                    if not file_size or not file_data:
                        res.update({"response": resp})
                        return res
                    binary_data = base64.b64decode(file_data)
                    # 保存本地文件
                    with open(output_file, 'wb') as f:
                        f.write(binary_data)
            if ('silk' == file_ext and not os.path.exists(f"{base_path}.mp3")) or fd:
                output_file = self.silk2mp3(output_file)
            file_url = f"{self.static_url}{fk}"
            file_md5 = self.vp_file_md5(output_file)
            res.update({
                "url": file_url,
                "md5": file_md5,
                "size": os.path.getsize(output_file),
            })
            return res
        except Exception as e:
            res.update({"code": 999, "msg": f"Download error: {e}"})
            return res

    def download_url_file(self, url, file_path):
        """下载并保存文件"""
        try:
            # 发送 HTTP 请求，设置 stream=True 以流式方式下载
            response = requests.get(url, stream=True, timeout=10)
            response.raise_for_status()
            with open(file_path, 'wb') as file:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        file.write(chunk)
            return file_path
        except requests.exceptions.RequestException as e:
            return ''

    def download_url_file_curl(self, url, file_path):
        """下载并保存文件 - curl"""
        try:
            # 通过curl下载
            if 0 == os.system(f'curl "{url}" --output {file_path}'):
                return file_path
            return ''
        except requests.exceptions.RequestException as e:
            return ''

    @staticmethod
    def vp_file_md5(file_path, chunk_size=8192):
        """获取文件的md5"""
        hash_obj = hashlib.md5()
        with open(file_path, 'rb') as f:
            while chunk := f.read(chunk_size):
                hash_obj.update(chunk)
        return hash_obj.hexdigest()

    @staticmethod
    def silk2mp3(file_path):
        """微信语音文件转mp3"""
        base_path, file_ext = str(file_path).rsplit('.', 1)
        if 0 == os.system(f'/opt/shell/tool/silk-v3-decoder/converter.sh {file_path} mp3'):
            # os.system(f'rm -f {file_path}')  # 暂时保留，也不占多少空间
            return f"{base_path}.mp3"
        return ''
