import os


class Cs7ShApi:
    """centos7 shell """

    @staticmethod
    def restart_gunicorn(p):
        """重启gunicorn"""
        sh = os.system(f'sudo /opt/shell/init/init_flask.sh >>/tmp/init_flask.log 2>&1')
        return {"p": p, "sh": sh}
