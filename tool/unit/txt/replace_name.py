import os
import re
from tool.core import *


class ReplaceName:
    @staticmethod
    def replace_names(input_file, replacement_dict):
        """
        将Txt文件中的姓名进行批量替换
        :param input_file: Txt文件路径，相对路径
        :param replacement_dict: 替换名字的数据字典
        """
        # 生成输出文件路径
        input_file = Dir.abs_dir(input_file)
        file_name, file_ext = os.path.splitext(input_file)
        output_file = f"{file_name}-cg{file_ext}"
        try:
            # 读取输入文件内容
            with open(input_file, 'r', encoding='utf-8') as file:
                lines = file.readlines()

            new_lines = []
            # 时间格式和人名的正则表达式
            pattern = re.compile(r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) (\S+)$')
            for line in lines:
                match = pattern.match(line)
                if match:
                    time_part = match.group(1)
                    name_part = match.group(2)
                    if name_part in replacement_dict:
                        # 符合替换条件，进行替换
                        new_name = replacement_dict[name_part]
                        line = f"{time_part} {new_name}\n"
                new_lines.append(line)
            # 将替换后的内容写入输出文件
            with open(output_file, 'w', encoding='utf-8') as file:
                file.writelines(new_lines)
            return Api.success({}, f"替换完成，结果已保存到 {output_file}")
        except FileNotFoundError:
            return Api.error(f"错误：未找到 {input_file} 文件。")
        except Exception as e:
            return Api.error(f"发生未知错误：{e}")
