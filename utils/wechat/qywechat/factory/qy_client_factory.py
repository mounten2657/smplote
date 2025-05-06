import requests
from tool.core import *

logger = Logger()


class QyClientFactory:

    _QY_CACHE_FILE = Dir.abs_dir('storage/tmp/qy_cache.json')
    _QY_API_BASE = 'https://qyapi.weixin.qq.com'
    _QY_API_ACCESS_TOKEN = '/cgi-bin/gettoken'

    def __init__(self, app_key):
        self.app_key = app_key
        self.config = Config.qy_config()
        self.corp_id = self.config.get('corp_id')
        self.corp_name = self.config.get('corp_name')
        self.refresh_config(app_key)

    def refresh_config(self, app_key):
        """刷新应用配置"""
        self.app_key = app_key
        self.app_config = self.config.get('app_list').get(self.app_key)
        self.agent_id = self.app_config.get('agent_id')
        self.app_secret = self.app_config.get('app_secret')
        self.user_list = self.app_config.get('user_list')

    def get_access_token(self):
        """获取 access token - 2个小时有效期"""
        # 先判断是否有缓存
        cache = File.read_file(self._QY_CACHE_FILE)
        mtime = 0 if not cache else cache.get('act').get('update_time')
        if Time.now() - mtime < 7200:
            return cache.get('act').get('access_token')
        # 没有缓存刷新接口
        url = f'{self._QY_API_ACCESS_TOKEN}?corpid={self.corp_id}&corpsecret={self.app_secret}'
        result = self.qy_http_request(url)
        if result.get('errcode') == 0:
            access_token = result.get('access_token')
            cache = cache if cache else {}
            cache.update({
                "act": {
                    "access_token": access_token,
                    "update_time": Time.now(),
                    "update_date": Time.date(),
                    "result": result
                }
            })
            File.save_file(cache, self._QY_CACHE_FILE, False)
            return result.get('access_token')
        else:
            return None

    def qy_http_request(self, url, data=None):
        """请求企业微信接口"""
        url = f'{self._QY_API_BASE}{url}'
        logger.info({"url":url, "data": data}, 'QY_API_STA')
        if not data:
            response = requests.get(url)
        else:
            response = requests.post(url, json=data)
        result = response.json()
        if result.get('errcode') == 0:
            logger.info({"url": url, "result": result}, 'QY_API_SUC')
            return result
        else:
            logger.error(f'request qy api failed - {url} - {result}', 'QY_API_ERR')
            return False

