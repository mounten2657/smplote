import json
import types
from collections import OrderedDict


class Attr:
    @staticmethod
    def get(data, key, default=None):
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
    def dict_to_obj(d):
        """字典转对象"""
        if isinstance(d, dict):
            for k, v in d.items():
                d[k] = Attr.dict_to_obj(v)
            return types.SimpleNamespace(**d)
        elif isinstance(d, list):
            return [Attr.dict_to_obj(x) for x in d]
        else:
            return d

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

    @staticmethod
    def get_value_by_key_like(d: dict, search_key: str, default='') -> any:
        """
        遍历字典，查找键名包含指定字符串（忽略大小写）的项，并返回对应的值。

        参数:
            d: 需要遍历的字典
            search_key: 需要查找的键名字符串（忽略大小写）
            default: 查找不到时返回的默认值

        返回:
            第一个匹配的键对应的值，如果没有匹配则返回None
        """
        if not isinstance(d, dict) or not isinstance(search_key, str):
            return default

        lower_search_key = search_key.lower()
        result = default

        for key, value in d.items():
            if isinstance(key, str) and lower_search_key in key.lower():
                result = value
                break

        return result

    @staticmethod
    def convert_to_json_dict(obj):
        """
        递归遍历对象，将里面的值对应的JSON字符串转换为字典/列表

        参数:
            obj: 任意类型的对象

        返回:
            处理后的对象，如果无法处理则返回原值
        """
        try:
            # 处理None
            if obj is None:
                return None
            # 处理字符串
            if isinstance(obj, str):
                # 尝试解析JSON
                try:
                    # 检查是否是JSON字符串（简单判断，避免解析普通字符串）
                    if (obj.startswith(('{', '[')) and obj.endswith(('}', ']'))):
                        return json.loads(obj)
                    return obj
                except (json.JSONDecodeError, TypeError):
                    return obj
            # 处理列表
            if isinstance(obj, list):
                return [Attr.convert_to_json_dict(item) for item in obj]
            # 处理元组（转换为列表以保持可变性）
            if isinstance(obj, tuple):
                return tuple(Attr.convert_to_json_dict(item) for item in obj)
            # 处理字典
            if isinstance(obj, dict):
                return {key: Attr.convert_to_json_dict(value) for key, value in obj.items()}
            # 其他类型（数字、布尔值等）直接返回
            return obj
        except Exception:
            # 捕获所有异常，返回原值
            return obj

    @staticmethod
    def convert_to_json_string(obj):
        """
        将对象中的字典转换为JSON字符串，并处理bytes类型数据

        参数:
            obj: 待处理的对象（字典、列表或其他类型）

        返回:
            处理后的对象
        """
        def process_value(value):
            """递归处理值"""
            if isinstance(value, bytes):
                try:
                    return value.decode('utf-8')
                except UnicodeDecodeError:
                    return str(value)
            elif isinstance(value, dict):
                return {k: process_value(v) for k, v in value.items()}
            elif isinstance(value, (list, tuple)):
                return [process_value(item) for item in value]
            return value

        try:
            # 处理字典
            if isinstance(obj, dict):
                new_dict = {}
                for key, value in obj.items():
                    processed_value = process_value(value)
                    if isinstance(processed_value, (dict, list, tuple)):
                        try:
                            new_dict[key] = json.dumps(processed_value, ensure_ascii=False)
                        except (json.JSONDecodeError, TypeError):
                            new_dict[key] = processed_value
                    else:
                        new_dict[key] = processed_value
                return new_dict

            # 处理列表或元组
            if isinstance(obj, (list, tuple)):
                processed_list = [process_value(item) for item in obj]
                return processed_list if isinstance(obj, list) else tuple(processed_list)

            # 其他类型直接返回
            return obj

        except Exception:
            return obj



