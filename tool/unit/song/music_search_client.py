from tool.unit.song.qq_music_search import QQMusicSearch
from tool.unit.song.wy_music_search import WYMusicSearch


class MusicSearchClient:
    """音乐搜索器"""

    def __init__(self, s_type='QQ'):
        self.s_type = s_type.upper()
        if 'QQ' == self.s_type:
            self.client = QQMusicSearch()
        elif 'WY' == self.s_type:
            self.client = WYMusicSearch()
        else:
            self.client = None

    def get_song_data(self, title, album=''):
        """
        获取歌曲的基本信息
        :param str title: 歌曲名
        :param str album: 自定义歌曲封面
        :return: 歌曲的基本信息
        """
        res = self.client.music_parse(title.strip())
        return {
            "id": res.get('id', 0),
            "name": res.get('name', ''),
            "singer_name": res.get('singer_name', ''),
            "song_url": res.get('song_url', ''),
            "data_url": res.get('data_url', ''),
            "album_img": album if album else res.get('album_img', album),
        }

    def get_song_xml(self, title, album=''):
        """
        获取xml结构内容 - 用于发送app消息
        :param str title: 歌曲名
        :param str album: 自定义歌曲封面
        :return: 歌曲的xml结构
        """
        try:
            res = self.get_song_data(title.strip(), album)
            if not res['song_url']:
                return ""
            xml = f"<appmsg appid='{self.client.appid}' sdkver='0'>  <title>{res['name']}</title>  <des>{res['singer_name']}</des>  <type>76</type>  <url>{res['song_url']}</url>  <lowurl></lowurl>  <dataurl>{res['data_url']}</dataurl>  <lowdataurl></lowdataurl>  <songalbumurl>{res['album_img']}</songalbumurl>  <songlyric></songlyric>  <appattach>    <cdnthumbaeskey/>    <aeskey/>  </appattach></appmsg>"
            return xml
        except Exception as e:
            return ''
