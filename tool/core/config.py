import json
from tool.core.env import Env
from tool.core.dir import Dir
from tool.core.file import File


class Config:

    WX_SQLITE_DIR = 'data/database/sqlite'
    WX_INFO_JSON = 'data/file/account/wx_info.json'

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
    def account_config():
        return Config.load_config('config/account.json')

    @staticmethod
    def ai_config():
        return Config.load_config('config/ai.json')

    @staticmethod
    def app_config():
        return Config.load_config('config/app.json')

    @staticmethod
    def logger_config():
        return Config.load_config('config/logger.json')

    @staticmethod
    def wx_config():
        config = Config.load_config('config/wx.json')
        return File.convert_to_abs_path(config, 'save_dir')

    @staticmethod
    def wx_info_config():
        return Config.load_config(Config.WX_INFO_JSON)

    @staticmethod
    def db_config(db_name='default'):
        config = Config.load_config('config/db.json').get(db_name)
        config['path'] = Dir.abs_dir(config['path'])
        return config





