from tool.router.base_app import BaseApp


class SendMsg(BaseApp):

    def auto_reply(self):
        data = {"params": self.params, 'root_dir': self.root_dir}
        return self.success(data)


