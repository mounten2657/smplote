from gewechat_client import GewechatClient
from tool.core import *

logger = Logger()


class GewechatClientFactory:
    """
    GewechatClient工厂类，负责创建和管理GewechatClient实例
    """
    _client_instance = None
    _is_logged_in = False
    _first_run = True
    
    @classmethod
    def get_client(cls, config) -> GewechatClient:
        """
        获取GewechatClient实例
        如果实例不存在，则创建一个新实例
        第一次执行时，如果检测到客户端已在线，则直接使用
        
        :param config: 配置字典，包含gewechat_base_url和gewechat_token
        :return: GewechatClient实例
        """
        if cls._client_instance is None:
            base_url = config.get('gewechat_base_url')
            token = config.get('gewechat_token')
            app_id = config.get('gewechat_app_id')
            if not base_url or not token:
                err_msg = "缺少必要的配置参数：gewechat_base_url 或 gewechat_token"
                logger.error(err_msg, 'GCF_ERR')
                raise RuntimeError(err_msg)
            cls._client_instance = GewechatClient(base_url, token)
            logger.debug(f"已创建GewechatClient实例，base_url: {base_url}")
            # 如果是第一次运行，检查登录状态
            if cls._first_run and app_id:
                cls._first_run = False
                try:
                    # 这里调用一个需要登录状态的API来检查是否在线
                    response = cls._client_instance.fetch_contacts_list(app_id)  # 备选方法： list_labels,  get_profile
                    if response.get('ret') == 200:
                        logger.debug("检测到客户端已在线，将继续使用当前会话")
                        cls._is_logged_in = True
                except Exception as e:
                    logger.debug(f"检查登录状态时发生错误: {e}")
                    # 发生错误时不设置登录状态，后续会通过 login_if_needed 处理
        return cls._client_instance
    
    @classmethod
    def login_if_needed(cls, client, app_id):
        """
        如果需要，执行登录操作
        
        :param client: GewechatClient实例
        :param app_id: 应用ID
        :return: 是否登录成功
        """
        if cls._is_logged_in:
            logger.debug("客户端已登录，无需重复登录")
            return True
        # 请关闭代理再执行登陆操作
        try:
            response = client.login(app_id=app_id)
        except Exception as e:
            logger.error(f"登录失败: {e}", 'GCF_ERR')
            return False
        if response.get('ret') == 200:
            logger.info(f"登录成功，app_id: {app_id}")
            cls._is_logged_in = True
            # 保存app_id
            Config.set_env('GEWECHAT_APP_ID', app_id)
            return True
    
    @classmethod
    def reset(cls):
        """重置工厂状态，用于测试或重新初始化"""
        cls._client_instance = None
        cls._is_logged_in = False
        cls._first_run = True

