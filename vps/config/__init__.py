import json
from pathlib import Path


class Config:

    @staticmethod
    def get_config(name):
        config_path = Path(__file__).parent / f"{name}.json"
        with open(config_path, 'r') as f:
            return json.load(f)

    @staticmethod
    def qy_config():
        return Config.get_config('qy')

