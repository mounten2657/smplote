import subprocess


class Sys:

    @staticmethod
    def run_command(command):
        result = subprocess.run(
            [
                'bash',
                '-c',
                f'{command}'
            ],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()


