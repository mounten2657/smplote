import subprocess


class Sys:

    @staticmethod
    def run_with_alias(command):
        # 执行 bash 并加载 .bashrc，然后执行别名命令
        result = subprocess.run(
            [
                'bash',
                '-c',
                f'source ~/.bashrc && {command}'
            ],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()


