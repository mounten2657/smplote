import os
import json
from tool.core.env import Env
from tool.core.dir import Dir
from tool.core.file import File


class Config:

    @staticmethod
    def load_config(config_path='config/app.json'):
        try:
            with open(Dir.abs_dir(config_path), 'r', encoding='utf-8') as file:
                config_data = json.load(file)
                config_data = Env.convert_config(config_data)
                return config_data
        except FileNotFoundError:
            print(f"未找到 {config_path} 文件，请检查文件是否存在。")
            return {}
        except json.JSONDecodeError:
            print(f"解析 {config_path} 文件时出错，请检查文件格式。")
            return {}

    @staticmethod
    def set_env(key: str, val, prefix=''):
        if prefix:
            prefix = prefix if prefix.endswith('_') else prefix + '_'
        key = prefix + key.upper()
        return Env.write_env(key, val)

    @staticmethod
    def is_prod():
        return int(os.environ.get('IS_PROD', 0))

    @staticmethod
    def base_url(is_prod=0):
        app = Config.app_config()
        if Config.is_prod() or is_prod:
            domain = Env.get('APP_SERVER_HOST', '', '.env.prod', True)
            not Config.is_prod() and Env.get('APP_SERVER_HOST', '', '.env', True)  # 恢复原样
            return f"https://{domain}"
        return f"http://{app['SERVER_HOST']}:{app['SERVER_PORT']}"

    @staticmethod
    def ai_config():
        return Config.load_config('config/ai.json')

    @staticmethod
    def app_config():
        config = Config.load_config('config/app.json')
        config['DEBUG'] = str(config['DEBUG']).lower() != 'false'
        return config

    @staticmethod
    def cache_config():
        return Config.load_config('config/cache.json')

    @staticmethod
    def redis_config():
        return Config.cache_config()['redis']

    @staticmethod
    def mysql_db_config(db_name='default'):
        return Config.load_config('config/db.json').get('mysql', {}).get(db_name)

    @staticmethod
    def sqlite_db_config(db_name='default'):
        config = Config.load_config('config/db.json').get('sqlite', {}).get(db_name)
        config['path'] = Dir.abs_dir(config['path'])
        return config

    @staticmethod
    def sqlite_db_dir(db_name='default'):
        return os.path.dirname(Config.sqlite_db_config(db_name)['path'])

    @staticmethod
    def gewechat_config():
        return Config.load_config('config/gewechat.json')

    @staticmethod
    def logger_config():
        return Config.load_config('config/logger.json')

    @staticmethod
    def qy_config():
        return Config.load_config('config/qy.json')

    @staticmethod
    def voice_config():
        return Config.load_config('config/voice.json')

    @staticmethod
    def vp_config():
        return Config.load_config('config/vp.json')

    @staticmethod
    def wx_config():
        config = Config.load_config('config/wx.json')
        return File.convert_to_abs_path(config, 'save_dir')


