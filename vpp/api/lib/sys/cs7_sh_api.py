import docker

class Cs7ShApi:
    """centos7 shell """

    @staticmethod
    def restart_gunicorn(p):
        """重启gunicorn"""
        client = docker.DockerClient(base_url='unix:///var/run/docker.sock')
        container = client.containers.get('www-python')
        res = container.restart()
        return {"p": p, "res": res}
