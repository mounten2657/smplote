import re
import json
import requests
from datetime import datetime
from tool.core import Config, Api, Attr


class QQMusicSearch:
    """QQ音乐搜索器"""

    def __init__(self):
        self.config = Config.qq_config()
        self.appid = self.config['appid']

    def music_parse(self, title):
        """
        获取歌曲基本信息
        :param srt title: 歌曲名
        :return:  歌曲信息
        """
        res = self.qq_music_search(title)
        res = Attr.get_by_point(res, 'data.data.0', {})
        if not res.get('song_url', ''):
            return {}
        return {
            "id": res.get('mid', 0),
            "name": res.get('name', ''),
            "singer_name": res.get('singer_name', ''),
            "song_url": res.get('song_url', ''),
            "data_url": res.get('data_url', ''),
            "album_img": res.get('album_img', ''),
        }

    def qq_music_search(self, msg, n=0, type_='song', page_limit=1, count_limit=3, song_id=None):
        """
        QQ 音乐搜索主函数
        :param str msg: 要解析的歌名
        :param int n: 选择的歌曲序号
        :param str type_: 解析类型，如 'song' 或 'songid'
        :param int page_limit: 页码
        :param int count_limit: 每页数量
        :param str song_id: 歌曲 ID
        :return: 解析结果的字典
        """
        if type_ == 'song':
            if not msg:
                return self._format_response(0, '请输入要解析的歌名', {})
            return self.get_qq_song(msg, page_limit, count_limit, n)
        elif type_ == 'songid':
            if song_id:
                json_data = self.get_mp3_data(song_id)
                song_url = json_data["songList"][0]["url"]
                data = {
                    'type': '歌曲解析',
                    'now': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'song_url': song_url
                }
                return self._format_response(0, '解析成功', data)
            return self._format_response(101, '解析失败，请检查歌曲id值是否正确', {'type': '歌曲解析'})
        else:
            return self._format_response(102, f'请求参数不存在{type_}', {})

    def get_qq_song(self, msg, page_limit, count_limit, n):
        """
        获取 QQ 歌曲信息
        :param str msg: 要解析的歌名
        :param int page_limit: 页码
        :param int count_limit: 每页数量
        :param int n: 选择的歌曲序号
        :return: 歌曲信息的字典
        """
        post_data = {
            "comm": self.config.get("comm", {}),
            "music.search.SearchCgiService": {
                "method": "DoSearchForQQMusicDesktop",
                "module": "music.search.SearchCgiService",
                "param": {
                    "grp": 1,
                    "num_per_page": count_limit,
                    "page_num": page_limit,
                    "query": msg,
                    "remoteplace": "txt.newclient.history",
                    "search_type": 0,
                    "searchid": "6254988708H54D2F969E5D1C81472A98609002"
                }
            }
        }
        headers = self.config.get("headers", {})
        post_url = self.config.get("post_url")
        if not post_url:
            raise ValueError("配置文件中缺少 post_url 信息。")

        response = requests.post(post_url, json=post_data, headers=headers)
        json_data = response.json()
        info_list = json_data["music.search.SearchCgiService"]["data"]["body"]["song"]["list"]
        data_list = []

        if n is not None:
            n = int(n)
            info = info_list[n]
            song_mid = info["mid"]
            song_url = None
            if song_mid:
                json_data2 = self.get_mp3_data(song_mid)
                song_url = json_data2["songList"][0]["url"]
            song_name = song_desc = info["name"]
            if not song_url:
                song_url = None
                song_desc = f"{song_name}[付费歌曲]"
            data_list = [
                {
                    "mid": song_mid,
                    "name": song_name,
                    "singer_name": info["singer"][0]["name"],
                    "song_desc": song_desc,
                    "mp3_url": song_url,
                    "song_url": f'http://c.y.qq.com/v8/playsong.html?songmid={song_mid}',
                    "album_img": f"https://y.qq.com/music/photo_new/T002R300x300M000{info['album']['pmid']}.jpg"
                }
            ]
        else:
            for info in info_list:
                data = {
                    "name": info["name"],
                    "singername": info["singer"][0]["name"],
                    "mid": info["mid"],
                    "vid": info['mv']['vid'] if info['mv']['vid'] else None,
                    "time_public": info['time_public'],
                }
                data_list.append(data)

        data = {
            'type': '歌曲解析',
            'now': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'data': data_list
        }
        return self._format_response(0, '解析成功', data)

    def get_mp3_data(self, song_mid):
        """
        获取 MP3 数据
        :param str song_mid: 歌曲的 MID
        :return: MP3 数据的字典
        """
        url_template = self.config.get("playsong_url_template")
        if not url_template:
            raise ValueError("配置文件中缺少 playsong_url_template 信息。")
        url = url_template.format(song_mid=song_mid)
        response = requests.get(url)
        html_str = response.text
        match = re.search(r'>window.__ssrFirstPageData__ =(.*?)</script', html_str)
        json_str = match.group(1)
        json_str = json_str.replace('undefined', '""')
        json_data = json.loads(json_str)
        return json_data

    def _format_response(self, code, msg, data):
        """
        统一数据返回格式
        :param code 整数: 状态码
        :param msg 字符串: 提示信息
        :param data 字典: 数据内容
        :return: 格式化后的响应字典
        """
        return Api.restful(data, msg, code)
