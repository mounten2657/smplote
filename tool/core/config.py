import json
import os
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
    def ai_config():
        return Config.load_config('config/ai.json')

    @staticmethod
    def app_config():
        return Config.load_config('config/app.json')

    @staticmethod
    def db_config(db_name='default'):
        config = Config.load_config('config/db.json').get(db_name)
        config['path'] = Dir.abs_dir(config['path'])
        return config

    @staticmethod
    def db_path(db_name='default'):
        config = Config.load_config('config/db.json').get(db_name)
        return Dir.abs_dir(config['path'])

    @staticmethod
    def db_dir(db_name='default'):
        return os.path.dirname(Config.db_path(db_name))

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
    def wx_config():
        config = Config.load_config('config/wx.json')
        return File.convert_to_abs_path(config, 'save_dir')


