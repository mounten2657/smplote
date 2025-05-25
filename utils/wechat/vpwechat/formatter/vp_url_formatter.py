from tool.core import Dir, Time, Config, File
from utils.wechat.vpwechat.vp_client import VpClient
import base64


class VpUrlFormatter:

    @staticmethod
    def get_img_url(message):
        """
        下载图片并返回可以访问的图片网址
        :param message:
        :return:
        """
        msg_id = message.get('p_msg_id')
        if not msg_id:
            return ''
        file_name = f"wechat/{'friend' if int(message['is_sl']) else f'room/{str(message['g_wxid']).split('@')[0]}'}"
        file_name += f"/{Time.date('%Y%m')}/{message['msg_id']}.png"
        local_file = Dir.abs_dir(f"storage/upload/{file_name}")
        base64_img = VpClient(message['app_key']).download_img(msg_id)
        if not base64_img:
            return ''
        if not File.save_file(base64_img, local_file, False, False):
            return ''
        return f"{Config.base_url(0)}/src/static/image/{file_name}"


