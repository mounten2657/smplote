import json
from collections import OrderedDict

class Attr:
    @staticmethod
    def get_attr(data, key, default=None):
        try:
            # 尝试以对象属性的方式获取值
            return getattr(data, key)
        except (AttributeError, TypeError):
            try:
                # 尝试以字典键的方式获取值
                return data[key]
            except (KeyError, TypeError):
                # 若都失败，返回默认值
                return default

    @staticmethod
    def has_keys(data, keys):
        for key in keys:
            try:
                if isinstance(data, dict):
                    if key not in data:
                        return False
                elif hasattr(data, '__getitem__'):
                    try:
                        _ = data[key]
                    except (KeyError, IndexError, TypeError):
                        return False
                else:
                    return False
            except Exception:
                return False
        return True

    @staticmethod
    def remove_keys(dictionary, keys):
        """
        从字典中移除指定的键
        :param dictionary: 输入的字典
        :param keys: 要移除的键的列表
        :return: 移除指定键后的字典
        """
        if not Attr.has_keys(dictionary, keys):
            return dictionary
        return {key: value for key, value in dictionary.items() if key not in keys}

    @staticmethod
    def parse_json_ignore(data):
        try:
            return json.loads(data)
        except (json.JSONDecodeError, TypeError) as e:
            return data

    @staticmethod
    def deduplicate_list(data, key):
        """对列表根据指定key进行去重"""
        # 使用OrderedDict去重（后出现的记录会覆盖前面的）
        deduplicated = OrderedDict()
        for item in data:
            deduplicated[item[key]] = item  # 相同key会覆盖
        # 转回列表
        return list(deduplicated.values())

    @staticmethod
    def select_item_by_where(data_list, where):
        """列表搜索"""
        return next((item for item in data_list if all(item.get(key) == value for key, value in where.items())), None)



