from tool.core import Str


class StockStrFormatterService:

    @staticmethod
    def extract_province_city(address: str):
        """
        从地址字符串中提取省份和城市（精确到地级市）
         - 1. 优先匹配省份，再匹配该省份下的城市
         - 2. 未匹配到则返回空字符串
         - 3. 支持直辖市自动填充（如上海→上海市）

        :param: address - 地址字符串
        :return: [省份, 城市]
        """
        # 中国省份列表（含简称）
        provinces = {
            '北京': ['北京市'],
            '上海': ['上海市'],
            '天津': ['天津市'],
            '重庆': ['重庆市'],
            '河北': ['石家庄', '唐山', '秦皇岛', '邯郸', '邢台', '保定', '张家口', '承德', '沧州', '廊坊', '衡水'],
            '山西': ['太原', '大同', '阳泉', '长治', '晋城', '朔州', '晋中', '运城', '忻州', '临汾', '吕梁'],
            '内蒙古': ['呼和浩特', '包头', '乌海', '赤峰', '通辽', '鄂尔多斯', '呼伦贝尔', '巴彦淖尔', '乌兰察布', '兴安', '锡林郭勒', '阿拉善'],
            '辽宁': ['沈阳', '大连', '鞍山', '抚顺', '本溪', '丹东', '锦州', '营口', '阜新', '辽阳', '盘锦', '铁岭', '朝阳', '葫芦岛'],
            '吉林': ['长春', '吉林', '四平', '辽源', '通化', '白山', '松原', '白城', '延边'],
            '黑龙江': ['哈尔滨', '齐齐哈尔', '鸡西', '鹤岗', '双鸭山', '大庆', '伊春', '佳木斯', '七台河', '牡丹江', '黑河', '绥化', '大兴安岭'],
            '江苏': ['南京', '无锡', '徐州', '常州', '苏州', '南通', '连云港', '淮安', '盐城', '扬州', '镇江', '泰州', '宿迁'],
            '浙江': ['杭州', '宁波', '温州', '嘉兴', '湖州', '绍兴', '金华', '衢州', '舟山', '台州', '丽水'],
            '安徽': ['合肥', '芜湖', '蚌埠', '淮南', '马鞍山', '淮北', '铜陵', '安庆', '黄山', '滁州', '阜阳', '宿州', '六安', '亳州', '池州', '宣城'],
            '福建': ['福州', '厦门', '莆田', '三明', '泉州', '漳州', '南平', '龙岩', '宁德'],
            '江西': ['南昌', '景德镇', '萍乡', '九江', '新余', '鹰潭', '赣州', '吉安', '宜春', '抚州', '上饶'],
            '山东': ['济南', '青岛', '淄博', '枣庄', '东营', '烟台', '潍坊', '济宁', '泰安', '威海', '日照', '临沂', '德州', '聊城', '滨州', '菏泽'],
            '河南': ['郑州', '开封', '洛阳', '平顶山', '安阳', '鹤壁', '新乡', '焦作', '濮阳', '许昌', '漯河', '三门峡', '南阳', '商丘', '信阳', '周口', '驻马店', '济源'],
            '湖北': ['武汉', '黄石', '十堰', '宜昌', '襄阳', '鄂州', '荆门', '孝感', '荆州', '黄冈', '咸宁', '随州', '恩施', '潜江'],
            '湖南': ['长沙', '株洲', '湘潭', '衡阳', '邵阳', '岳阳', '常德', '张家界', '益阳', '郴州', '永州', '怀化', '娄底', '湘西'],
            '广东': ['广州', '韶关', '深圳', '珠海', '汕头', '佛山', '江门', '湛江', '茂名', '肇庆', '惠州', '梅州', '汕尾', '河源', '阳江', '清远', '东莞', '中山', '潮州', '揭阳', '云浮'],
            '广西': ['南宁', '柳州', '桂林', '梧州', '北海', '防城港', '钦州', '贵港', '玉林', '百色', '贺州', '河池', '来宾', '崇左'],
            '海南': ['海口', '三亚', '三沙', '儋州'],
            '四川': ['成都', '自贡', '攀枝花', '泸州', '德阳', '绵阳', '广元', '遂宁', '内江', '乐山', '南充', '眉山', '宜宾', '广安', '达州', '雅安', '巴中', '资阳', '阿坝','甘孜', '凉山'],
            '贵州': ['贵阳', '六盘水', '遵义', '安顺', '毕节', '铜仁', '黔西南', '黔东南', '黔南'],
            '云南': ['昆明', '曲靖', '玉溪', '保山', '昭通', '丽江', '普洱', '临沧', '楚雄', '红河', '文山', '西双版纳', '大理', '德宏', '怒江', '迪庆'],
            '西藏': ['拉萨', '日喀则', '昌都', '林芝', '山南', '那曲', '阿里'],
            '陕西': ['西安', '铜川', '宝鸡', '咸阳', '渭南', '延安', '汉中', '榆林', '安康', '商洛'],
            '甘肃': ['兰州', '嘉峪关', '金昌', '白银', '天水', '武威', '张掖', '平凉', '酒泉', '庆阳', '定西', '陇南', '临夏', '甘南'],
            '青海': ['西宁', '海东', '海北', '黄南', '海南', '果洛', '玉树', '海西'],
            '宁夏': ['银川', '石嘴山', '吴忠', '固原', '中卫'],
            '新疆': ['乌鲁木齐', '克拉玛依', '吐鲁番', '哈密', '昌吉', '博州', '巴州', '阿克苏', '克州', '喀什', '和田', '伊犁', '塔城', '阿勒泰', '石河子', '五家渠', '阿拉尔', '图木舒克', '可克达拉', '双河', '胡杨河', '北屯', '铁门关', '新星'],
            '台湾': ['台北', '新北', '桃园', '台中', '台南', '高雄', '基隆', '新竹', '嘉义'],
            '香港': ['香港'],
            '澳门': ['澳门']
        }
        # 标准化地址（去除空格和不可打印字符）
        clean_addr = ''.join(c for c in address.strip() if c.isprintable())
        # 遍历省份匹配
        for p, cities in provinces.items():
            # 在该省份下匹配城市
            for c in cities:
                if c in clean_addr:
                    city, province = c, p
                    # city = c + ('市' if not c.endswith('市') else '')
                    # if p in ['北京', '上海', '天津', '重庆']:
                    #     province = p
                    # elif p in ['香港', '澳门']:
                    #     city = c
                    #     province = p + '特别行政区'
                    # else:
                    #     province = p + '省'
                    return [province, city]

        # 未匹配到则返回空
        return ['', '']

    @staticmethod
    def add_stock_prefix(stock_code):
        """
        根据股票代码自动添加交易所前缀（支持多市场）
         - A股：6: SH | 0, 3: SZ | 4, 8, 9: BJ  长度=6
         - B股：900/200开头（沪B/深B）或 SHB/SZB 前缀
         - 港股：5位数字或.HK结尾
         - 美股：1-5位字母或.US/.NYSE/.NASDAQ结尾
         - 中概股：特殊代码（如BABA）或.US结尾

        :param: stock_code -- 股票代码（支持int/str类型）
        :return: 带前缀的股票代码字符串
        """
        if not isinstance(stock_code, (str, int)):
            return stock_code
        code_str = str(stock_code).strip().upper()
        # 如果已有前缀，直接返回
        sgl = ['SHB', 'SZB', 'BJ', 'SH', 'SZ', 'HK', 'US', 'NYSE', 'NASDAQ', '.']
        if any(s in code_str for s in sgl):
            return code_str
        # 1. 检查B股（优先级最高）
        if (code_str.startswith(('900', '200')) and len(code_str) == 6) or \
                (len(code_str) == 3 and code_str.isdigit() and code_str.startswith(('9', '2'))):
            if code_str.startswith('900') or (len(code_str) == 3 and code_str.startswith('9')):
                code_str = f"SHB{code_str[-3:]}" if len(code_str) == 6 else f"SHB{code_str}"
            elif code_str.startswith('200') or (len(code_str) == 3 and code_str.startswith('2')):
                code_str = f"SZB{code_str[-3:]}" if len(code_str) == 6 else f"SZB{code_str}"
            return code_str
        # 2. 检查A股
        if len(code_str) == 6 and code_str.isdigit():
            if code_str[0] == '6':
                code_str = f"SH{code_str}"
            elif code_str[0] in ('0', '3'):
                code_str = f"SZ{code_str}"
            elif code_str[0] in ('4', '8', '9'):
                code_str = f"BJ{code_str}"
            return code_str
        # 3. 检查港股（5位数字或.HK结尾）
        if (len(code_str) == 5 and code_str.isdigit()) or code_str.endswith('.HK'):
            return code_str.split('.')[0] + '.HK'
        # 4. 检查美股（字母或.US/.NYSE结尾）
        if code_str.isalpha() or any(code_str.endswith(ext) for ext in ('.US', '.NYSE', '.NASDAQ')):
            return code_str.split('.')[0] + '.US'
        # 5. 中概股特殊处理（如BABA->BABA.US）
        if len(code_str) <= 5 and code_str.isalpha():
            return f"{code_str}.US"
        # 无法识别则原样返回
        return code_str

    @staticmethod
    def remove_stock_prefix(stock_symbol):
        """去除市场标识"""
        stock_symbol = str(stock_symbol).upper()
        sgl = ['SHB', 'SZB', 'BJ', 'SH', 'SZ', 'HK', 'US', 'NYSE', 'NASDAQ', '.']
        return Str.replace_multiple(stock_symbol, sgl)

    @staticmethod
    def get_stock_prefix(stock_code):
        """获取市场标识"""
        stock_code = StockStrFormatterService.remove_stock_prefix(stock_code)
        stock_symbol = StockStrFormatterService.add_stock_prefix(stock_code)
        return stock_symbol.replace(stock_code, '').replace('.', '')
