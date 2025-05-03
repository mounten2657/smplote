from tool.router.router_handler import RouterHandler

# 使用 WSGI 协议启动
router = RouterHandler()
app = router.get_app()
