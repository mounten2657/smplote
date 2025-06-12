import re
import json
import types
import importlib
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
        keys = keys if isinstance(keys, list) else [keys]
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
    def select_keys(d, fields):
        """
        返回字典中存在的指定字段
        :param d:  字典
        :param fields:  字段列表
        :return:  筛选后的字典
        """
        return {k: d[k] for k in fields if k in d}

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
    def get_by_point(data, path, default = None):
        """
        通过点表示法路径访问嵌套数据结构中的值

        参数:
            data: 嵌套的字典或列表
            path: 点表示法路径，如 "aaa.bbb.ccc"

        返回:
            指定路径的值，若路径不存在则返回 None
        """
        if not path:
            return data
        # 分割路径为组件列表
        components = path.split('.')
        try:
            # 逐级访问数据结构
            current = data
            for component in components:
                # 处理索引（如 "0" 转换为整数 0）
                if component.isdigit():
                    current = current[int(component)]
                else:
                    current = current[component]
            return current
        except (KeyError, IndexError, TypeError, ValueError):
            return default

    @staticmethod
    def parse_json_ignore(data):
        try:
            return json.loads(data)
        except (json.JSONDecodeError, TypeError) as e:
            return data

    @staticmethod
    def get_action_by_path(path, ins=0, *args, **kwargs):
        """
        通过路径自动加载类文件
        :param path: 类路径，如: from_path@class_name.action_name
        :param ins: 是否返回实例
        :return: 默认返回的一个可执行的类属性 - action()
        """
        module_path, method_fullname = path.split('@')
        class_name, method_name = method_fullname.split('.')
        module = importlib.import_module(module_path)
        cls = getattr(module, class_name)
        obj = cls(*args, **kwargs)
        action = Attr.get(obj, method_name)
        return action if not ins else (action, obj)

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
    def select_item_by_where(data_list, where, default=None):
        """列表搜索"""
        return next((item for item in data_list if all(item.get(key) == value for key, value in where.items())), default)

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

    @staticmethod
    def data_diff(dict1, dict2, lk='id', fm=1):
        """
        比较两个字典的共有字段差异，返回格式化差异结果
        列表处理逻辑：基于指定键(lk)匹配元素，简化差异描述
        input:
        a1 = {
            "k1": "v1", "k2": "v2", "k3": "v3", "k4": "v4",
            "k5": {"id": 10, "name": "n1", "age": 18, "score": 99},
            "k6": "v6",
            "k7": [{"id": 11, "name": "v11"}, {"id": 12, "name": "v12"}, {"id": 13, "name": "v13"}],
            "k9": '90.01'
        }
        a2 = {
            "k2": "v2", "k3": "v33",
            "k5": {"id": 10, "name": "n2", "age": 19},
            "k7": [{"id": 11, "name": "v11"}, {"id": 12, "name": "v13"}, {"id": 14, "name": "v14"}, {"id": 15, "name": "v15"}],
            "k8": "v8",
            "k9": '98.01'
        }
        output:
        {
          "k3": {"type": "str","val": "v3-->v33"},
          "k5": {"type": "dict","val": "age:18-->19||name:n1-->n2||score:99-->"},
          "k7": {"type": "list","val": "1.name:v12-->v13||2.id;name:13;v13-->||3.id;name:-->14;v14||4.id;name:-->15;v15"},
          "k9": {"type": "float","val": "90.01-->98.01"}
        }
        format:
        {'k3': 'v3-->v33', 'k5': 'name:n1-->n2||age:18-->19||score:99-->', 'k7': '1.name:v12-->v13||2.id;name:13;v13-->||3.id;name:-->14;v14||4.id;name:-->15;v15', 'k9': '90.01-->98.01'}

        参数:
            dict1 (dict): 第一个字典
            dict2 (dict): 第二个字典
            lk (str): 列表元素的匹配键名，默认为'id'
            fm (int): 是否简化返回，默认为 1

        返回:
            dict: 差异结果，格式为 {"字段名": {"type": 类型, "val": "差异描述"}}
        """
        diff_result = {}

        common_keys = set(dict1.keys()) & set(dict2.keys())

        for key in common_keys:
            val1 = dict1[key]
            val2 = dict2[key]

            if type(val1) != type(val2):
                diff_result[key] = {
                    "type": "type_mismatch",
                    "val": f"{type(val1).__name__}-->{type(val2).__name__}"
                }
                continue

            if isinstance(val1, dict):
                dict_diff = {}
                for sub_key in set(val1.keys()) | set(val2.keys()):
                    if sub_key in val1 and sub_key in val2:
                        if val1[sub_key] != val2[sub_key]:
                            dict_diff[sub_key] = f"{val1[sub_key]}-->{val2[sub_key]}"
                    elif sub_key in val1:
                        dict_diff[sub_key] = f"{val1[sub_key]}-->"
                    else:
                        dict_diff[sub_key] = f"-->{val2[sub_key]}"

                if dict_diff:
                    diff_result[key] = {
                        "type": "dict",
                        "val": "||".join([f"{k}:{v}" for k, v in dict_diff.items()])
                    }

            elif isinstance(val1, list):
                # 处理字典列表（有匹配键的情况）
                if all(isinstance(x, dict) and lk in x for x in val1 + val2):
                    # 构建匹配键到元素的映射
                    dict1_items = {x[lk]: x for x in val1}
                    dict2_items = {x[lk]: x for x in val2}

                    common_ids = set(dict1_items.keys()) & set(dict2_items.keys())
                    removed_ids = set(dict1_items.keys()) - common_ids
                    added_ids = set(dict2_items.keys()) - common_ids

                    list_diff = []
                    max_index = len(val1) - 1

                    # 处理修改的元素
                    for id_ in common_ids:
                        elem1 = dict1_items[id_]
                        elem2 = dict2_items[id_]

                        diff_fields = []
                        all_keys = set(elem1.keys()) | set(elem2.keys())
                        changed = False

                        for k in all_keys:
                            if k in elem1 and k in elem2:
                                if elem1[k] != elem2[k]:
                                    diff_fields.append(f"{k}:{elem1[k]}-->{elem2[k]}")
                                    changed = True
                            elif k in elem1:
                                diff_fields.append(f"{k}:{elem1[k]}-->")
                                changed = True
                            else:
                                diff_fields.append(f"{k}:-->{elem2[k]}")
                                changed = True

                        if changed:
                            original_index = next(i for i, x in enumerate(val1) if x[lk] == id_)
                            list_diff.append(f"{original_index}.{'||'.join(diff_fields)}")

                    # 处理删除的元素
                    for id_ in removed_ids:
                        elem = dict1_items[id_]
                        original_index = next(i for i, x in enumerate(val1) if x[lk] == id_)
                        field_str = ";".join(f"{k}" for k, v in elem.items())
                        value_str = ";".join(f"{v}" for k, v in elem.items())
                        list_diff.append(f"{original_index}.{field_str}:{value_str}-->")

                    # 处理新增的元素
                    for id_ in added_ids:
                        elem = dict2_items[id_]
                        new_index = max_index + 1 + len([x for x in added_ids if list(dict2_items.keys()).index(x) < list(dict2_items.keys()).index(id_)])
                        field_str = ";".join(f"{k}" for k, v in elem.items())
                        value_str = ";".join(f"{v}" for k, v in elem.items())
                        list_diff.append(f"{new_index}.{field_str}:-->{value_str}")

                    if list_diff:
                        diff_result[key] = {
                            "type": "list",
                            "val": "||".join(list_diff)
                        }
                else:
                    # 非字典列表或没有匹配键的情况
                    list_diff = []
                    min_len = min(len(val1), len(val2))

                    for i in range(min_len):
                        if val1[i] != val2[i]:
                            if isinstance(val1[i], dict) and isinstance(val2[i], dict):
                                sub_diff = []
                                for k in set(val1[i].keys()) | set(val2[i].keys()):
                                    if k in val1[i] and k in val2[i]:
                                        if val1[i][k] != val2[i][k]:
                                            sub_diff.append(f"{k}:{val1[i][k]}-->{val2[i][k]}")
                                    elif k in val1[i]:
                                        sub_diff.append(f"{k}:{val1[i][k]}-->")
                                    else:
                                        sub_diff.append(f"{k}:-->{val2[i][k]}")

                                if sub_diff:
                                    list_diff.append(f"{i}.{'||'.join(sub_diff)}")
                            else:
                                list_diff.append(f"{i}.{val1[i]}-->{val2[i]}")

                    if len(val1) > len(val2):
                        for i in range(len(val2), len(val1)):
                            list_diff.append(f"{i}.{val1[i]}-->")
                    elif len(val2) > len(val1):
                        for i in range(len(val1), len(val2)):
                            list_diff.append(f"{i}.-->{val2[i]}")

                    if list_diff:
                        diff_result[key] = {
                            "type": "list",
                            "val": "||".join(list_diff)
                        }

            elif val1 != val2:
                diff_result[key] = {
                    "type": type(val1).__name__,
                    "val": f"{val1}-->{val2}"
                }

        if fm:
            return {k: diff_result[k]["val"] for k in sorted(diff_result.keys(), key=lambda x: [int(c) if c.isdigit() else c for c in re.split('([0-9]+)', x)])}
        return diff_result

    @staticmethod
    def chunk_ids(d_list, size=20, key='wxid'):
        """
        从字典列表中提取指定键的值并按指定大小分块

        :param list d_list: 包含字典的列表，每个字典应包含指定的键
        :param int size: 每块的最大元素数量，默认为20
        :param str key: 要提取的键名，默认为 wxid
        :return list: 分块后的结果列表，每个子列表包含指定数量的键值
        """
        # 提取所有指定键的值
        wxid_list = [item.get(key) for item in d_list if key in item]
        # 分块处理
        chunked_result = []
        for i in range(0, len(wxid_list), size):
            chunked_result.append(wxid_list[i:i + size])
        return chunked_result
