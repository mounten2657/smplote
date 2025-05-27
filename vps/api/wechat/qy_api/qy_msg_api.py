import requests
from datetime import datetime, timedelta
from vps.base.desc import ConfigCrypto
from vps.config import Config


class QYMsgApi:
    def __init__(self, master_key: str):
        self.crypto = ConfigCrypto(master_key)
        self.config = self._load_config()
        self.token_cache = {}

    def _load_config(self):
        raw_config = Config.qy_config()
        return {
            'corp_id': self.crypto.decrypt(raw_config['corp_id']),
            'apps': {
                app_key: {
                    **app,
                    'agent_id': self.crypto.decrypt(app['agent_id']),
                    'app_secret': self.crypto.decrypt(app['app_secret'])
                }
                for app_key, app in raw_config['app_list'].items()
            }
        }

    def _get_access_token(self, app_key: str) -> str:
        # 检查缓存
        if app_key in self.token_cache:
            expires_at, token = self.token_cache[app_key]
            if datetime.now() < expires_at:
                return token

        # 重新获取token
        app = self.config['apps'][app_key]
        url = f"https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid={self.config['corp_id']}&corpsecret={app['app_secret']}"
        resp = requests.get(url).json()

        if resp['errcode'] != 0:
            raise Exception(f"Failed to get token: {resp}")

        # 缓存token（提前120秒过期）
        expires_at = datetime.now() + timedelta(seconds=resp['expires_in'] - 120)
        self.token_cache[app_key] = (expires_at, resp['access_token'])
        return resp['access_token']

    def send_text_message(self, content: str, app_key: str, user_list=None):
        token = self._get_access_token(app_key)
        app = self.config['apps'][app_key]

        url = f"https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={token}"
        payload = {
            "touser": user_list or self.crypto.decrypt(app['user_list']),
            "msgtype": "text",
            "agentid": int(app['agent_id']),
            "text": {"content": content},
            "safe": 0
        }

        resp = requests.post(url, json=payload).json()
        if resp['errcode'] != 0:
            print(f"Message send failed: {resp}")
            return resp
        return resp
