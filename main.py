from tool.router import ParseHandler, RouterHandler

"""
两种执行方式，命令行 和 http 请求：
  - python main.py -m bot.index.index -p "a=1x&b=2c" - python main.py --help 查看帮助
  - curl "http://localhost:9090/bot/index/index?a=1x&b=2c" - 需要先执行 python main.py
"""

if __name__ == "__main__":
    args = ParseHandler.parse_args()
    if args.method:  # 命令行模式
        ParseHandler().run_app()
    else:  # http 模式
        RouterHandler().run_app()
