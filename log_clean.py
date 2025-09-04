import re
import sys
import shutil
from pathlib import Path
from datetime import datetime, timedelta


def clean_old_logs(retain_days=7):
    """
    清理旧的日志文件和文件夹，保留指定天数内的文件

    Args:
        retain_days (int): 需要保留的天数，默认保留最近7天
    """
    # 计算截止日期
    cutoff_date = datetime.now() - timedelta(days=retain_days)
    print(f"清理日志文件，保留最近 {retain_days} 天的数据({cutoff_date.strftime('%Y-%m-%d')} 之后)")

    # 项目根目录
    base_dir = Path(__file__).parent

    # 需要清理的路径模式
    targets = [
        {
            'path': base_dir / 'storage' / 'logs',
            'pattern': r'^(\d{8})$',  # 匹配 20250101 格式的文件夹
            'type': 'folder',
            'date_format': '%Y%m%d'
        },
        {
            'path': base_dir / 'storage' / 'tmp',
            'pattern': r'^nohup_(\d{4}-\d{2}-\d{2})\.out$',  # 匹配 nohup_2025-01-01.out 格式的文件
            'type': 'file',
            'date_format': '%Y-%m-%d'
        }
    ]

    total_cleaned = 0

    for target in targets:
        if not target['path'].exists():
            print(f"路径不存在: {target['path']}")
            continue

        print(f"\n检查路径: {target['path']}")

        if target['type'] == 'folder':
            cleaned_count = _clean_folders(target['path'], target['pattern'],
                                           target['date_format'], cutoff_date)
        else:
            cleaned_count = _clean_files(target['path'], target['pattern'],
                                         target['date_format'], cutoff_date)

        total_cleaned += cleaned_count

    print(f"\n清理完成！共清理了 {total_cleaned} 个项目")
    return total_cleaned


def _clean_folders(folder_path, pattern, date_format, cutoff_date):
    """清理符合条件的文件夹"""
    cleaned_count = 0

    for item in folder_path.iterdir():
        if not item.is_dir():
            continue

        match = re.match(pattern, item.name)
        if match:
            try:
                # 提取日期字符串并解析
                date_str = match.group(1)
                folder_date = datetime.strptime(date_str, date_format)

                # 检查是否超过保留期限
                if folder_date.date() < cutoff_date.date():
                    print(f"删除过期文件夹: {item}")
                    shutil.rmtree(item)
                    cleaned_count += 1
                else:
                    print(f"保留文件夹: {item.name} (日期: {date_str})")

            except ValueError as e:
                print(f"解析文件夹日期失败: {item.name} - {e}")
            except Exception as e:
                print(f"删除文件夹失败: {item} - {e}")

    return cleaned_count


def _clean_files(folder_path, pattern, date_format, cutoff_date):
    """清理符合条件的文件"""
    cleaned_count = 0

    for item in folder_path.iterdir():
        if not item.is_file():
            continue

        match = re.match(pattern, item.name)
        if match:
            try:
                # 提取日期字符串并解析
                date_str = match.group(1)
                file_date = datetime.strptime(date_str, date_format)

                # 检查是否超过保留期限
                if file_date.date() < cutoff_date.date():
                    print(f"删除过期文件: {item}")
                    item.unlink()  # 删除文件
                    cleaned_count += 1
                else:
                    print(f"保留文件: {item.name} (日期: {date_str})")

            except ValueError as e:
                print(f"解析文件日期失败: {item.name} - {e}")
            except Exception as e:
                print(f"删除文件失败: {item} - {e}")

    return cleaned_count


if __name__ == "__main__":
    d = int(sys.argv[1]) if len(sys.argv) > 1 else 7
    print(f'开始清理日志，保留天数： {d} 天')
    clean_old_logs(d)
