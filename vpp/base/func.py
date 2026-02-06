import json


class Func:

    @staticmethod
    def str_to_json(s):
        """字符串转json"""
        try:
            return json.loads(s)
        except Exception as e:
            return s

