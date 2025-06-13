import importlib
from typing import List, Any


class Transfer:

    @staticmethod
    def middle_exec(desc: str, np: List[Any] = None, *args, **kwargs) -> Any:
        """
        中间执行器 - 用于解决循环引用问题的方法调度

        :param str desc: 目标方法描述，格式为"模块名.类名.方法名"
        :param list np: 实例化类时的参数列表
        :param args: 目标方法的位置参数
        :param kwargs: 目标方法的关键字参数
        :return: 目标方法的执行结果

        示例: Transfer.middle_exec('b.BClass.send_msg', np=['a2'], msg='xxx')
        """
        if np is None:
            np = []
        try:
            # 解析目标方法路径
            module_name, class_name, method_name = desc.rsplit('.', 2)
            print(module_name, class_name, method_name)
            # 动态导入模块
            module = importlib.import_module(module_name)
            class_ = getattr(module, class_name)
            # 实例化类（如果需要）
            if hasattr(class_, '__init__'):
                instance = class_(*np)
            else:
                instance = class_() if not np else class_(*np)
            # 获取目标方法
            method = getattr(instance, method_name)
            # 执行方法并返回结果
            return method(*args, **kwargs)
        except Exception as e:
            print(f"[ERROR]方法调用失败 - {e}")
            raise
