import json
import random
import requests
import binascii
import base64
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from tool.core import Config, Api, Attr, Error


class WYMusicSearch:
    """网易音乐搜索器"""

    def __init__(self):
        self.config = Config.wy_config()
        self.appid = self.config['appid']
        self.preset_key = self.config['preset_key']
        self.iv = f"0{self.config['iv']}"
        self.pub_key = f"0{self.config['pub_key']}"
        self.modulus = self.config['modulus']

    def music_parse(self, title):
        """
        获取歌曲基本信息
        :param srt title: 歌曲名
        :return:  歌曲信息
        """
        res = self.wy_music_search(title)
        res = Attr.get_by_point(res, 'data.result.songs.0', {})
        sid = res.get('id', 0)
        if not sid:
            return {}
        # song_url 备选 - 'https://y.music.163.com/m/song?id={sid}'
        return {
            "id": sid,
            "name": res.get('name', ''),
            "singer_name": Attr.get_by_point(res, 'ar.0.name', ''),
            "song_url": f'https://music.163.com/#/song?id={sid}',
            "data_url": f'https://music.163.com/song/media/outer/url?id={sid}.mp3',
            "album_img": Attr.get_by_point(res, 'al.picUrl', ''),
        }

    def generate_random_ip(self):
        """
        生成随机 IP 地址
        :return: 随机 IP 地址
        """
        ip2id = random.randint(0, 255)
        ip3id = random.randint(0, 255)
        ip4id = random.randint(0, 255)
        arr_1 = ["218", "218", "66", "66", "218", "218", "60", "60", "202", "204", "66", "66", "66", "59", "61", "60", "222", "221", "66", "59", "60", "60", "66", "218", "218", "62", "63", "64", "66", "66", "122", "211"]
        return f"{random.choice(arr_1)}.{ip2id}.{ip3id}.{ip4id}"

    def generate_random_user_agent(self):
        """
        生成随机 User-Agent
        :return: 随机 User-Agent
        """
        agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:92.0) Gecko/20100101 Firefox/92.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36",
            "Mozilla/5.0 (Linux; Android 13; Redmi Note 12 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"
        ]
        return random.choice(agents)

    def aes_encrypt(self, text, key):
        """
        AES 加密
        :param str text: 待加密文本
        :param str key: 加密密钥
        :return: 加密后的文本
        """
        cipher = AES.new(str(key).encode('utf-8'), AES.MODE_CBC, str(self.iv).encode('utf-8'))
        padded_text = pad(text.encode('utf-8'), AES.block_size)
        encrypted_text = cipher.encrypt(padded_text)
        return base64.b64encode(encrypted_text).decode('utf-8')

    def rsa_encrypt(self, text, pub_key, modulus):
        """
        RSA 加密
        :param str text: 待加密文本
        :param str pub_key: 公钥
        :param str modulus: 模数
        :return: 加密后的文本
        """
        text = text[::-1]
        bi_text = int(binascii.hexlify(text.encode('utf-8')), 16)
        bi_pub_key = int(str(pub_key), 16)
        bi_modulus = int(modulus, 16)
        bi_ret = pow(bi_text, bi_pub_key, bi_modulus)
        return hex(bi_ret)[2:].zfill(256)

    def encrypt_params(self, data):
        """
        加密请求参数
        :param dict data: 请求数据
        :return: 加密后的参数
        """
        secret_key = ''.join(random.choices('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=16))
        json_str = json.dumps(data)
        params = self.aes_encrypt(json_str, str(self.preset_key))
        params = self.aes_encrypt(params, secret_key)
        enc_sec_key = self.rsa_encrypt(secret_key, self.pub_key, self.modulus)
        return {
            'params': params,
            'encSecKey': enc_sec_key
        }

    def send_request(self, url, data, headers):
        """
        发送 HTTP 请求
        :param str url: 请求 URL
        :param dict data: 请求数据
        :param dict headers: 请求头
        :return: 响应结果
        """
        try:
            response = requests.post(url, data=data, headers=headers, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise Exception(f'请求失败: {str(e)}')
        except json.JSONDecodeError:
            raise Exception('解析响应失败')

    def search_music(self, keywords, limit=10, offset=0, type_=1):
        """
        搜索音乐
        :param str keywords: 搜索关键词
        :param int limit: 返回结果数量
        :param int offset: 偏移量
        :param int type_: 搜索类型，1 为单曲
        :return: 搜索结果
        """
        # 构建请求数据
        data = {
            's': keywords,
            'limit': limit,
            'offset': offset,
            'type': type_
        }
        # 加密参数
        encrypted_data = self.encrypt_params(data)
        # 生成随机 IP 和 User-Agent
        random_ip = self.generate_random_ip()
        random_user_agent = self.generate_random_user_agent()
        # 构建请求头
        headers = {
            'User-Agent': random_user_agent,
            'Connection': 'Keep-Alive',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Referer': 'http://music.163.com',
            'X-Real-IP': random_ip,
            'Client-IP': random_ip,
            'X-Forwarded-For': random_ip
        }
        # 发送请求到网易云音乐 API
        response = self.send_request('http://music.163.com/weapi/cloudsearch/pc', encrypted_data, headers)
        return response

    def get_lyric(self, id_):
        """
        获取歌词
        :param str id_: 歌曲 ID
        :return: 歌词结果
        """
        # 构建请求数据
        data = {
            'id': id_,
            'lv': -1,
            'tv': -1
        }
        # 加密参数
        encrypted_data = self.encrypt_params(data)
        # 生成随机 IP 和 User-Agent
        random_ip = self.generate_random_ip()
        random_user_agent = self.generate_random_user_agent()
        # 构建请求头
        headers = {
            'User-Agent': random_user_agent,
            'Connection': 'Keep-Alive',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Referer': 'http://music.163.com',
            'X-Real-IP': random_ip,
            'Client-IP': random_ip,
            'X-Forwarded-For': random_ip
        }
        # 发送请求到网易云音乐歌词 API
        response = self.send_request('http://music.163.com/weapi/song/lyric', encrypted_data, headers)
        return response

    def wy_music_search(self, name='', type_='search', limit=3, id_=''):
        """
        音乐解析方法
        :param str name: 歌曲名称
        :param str type_: 请求类型，search-搜索歌曲，lyric-获取歌词，默认 search
        :param int limit: 返回结果数量，默认 3，范围 1-100
        :param str id_: 歌曲 ID，用于获取歌词
        :return: 统一格式的结果
        """
        try:
            if type_ == 'lyric':
                if not id_:
                    return Api.error("请提供歌曲 ID", {}, 201)
                result = self.get_lyric(id_)
            else:
                if not name:
                    return Api.error("请提供歌曲名称", {}, 202)
                limit = max(1, min(100, limit))
                result = self.search_music(name, limit)
            return Api.success(result)
        except Exception as e:
            err = Error.handle_exception_info(e)
            return Api.error(str(e), err, 203)
