from service.gpl.gpl_formatter_service import GplFormatterService
from model.gpl.gpl_symbol_model import GPLSymbolModel
from model.gpl.gpl_symbol_ext_model import GPLSymbolExtModel
from model.gpl.gpl_season_model import GPLSeasonModel
from model.gpl.gpl_const_kv_model import GPLConstKvModel
from model.gpl.gpl_concept_model import GPLConceptModel
from model.gpl.gpl_symbol_text_model import GPLSymbolTextModel
from tool.core import Ins, Logger, Str, Time, Attr

logger = Logger()


@Ins.singleton
class GPLUpdateEccService:
    """股票更新附属类 - 概念板块"""

    _INIT_ST = GplFormatterService.INIT_ST
    _INIT_ET = GplFormatterService.INIT_ET

    def __init__(self):
        self.formatter = GplFormatterService()

    def update_by_xq(self, symbol, info, k_list_xq, c_list_xq):
        """从雪球中拉取数据进行更新"""
        res = {}
        # 改为只更新一次 - 毕竟不常用
        if k_list_xq and c_list_xq:
            return res
        code = info['code']
        stock = self.formatter.get_stock_info(code, 1)
        if stock:
            concept_code = Attr.get(stock, 'concept_code_xq', '')
            concept_name = Attr.get(stock, 'concept_name_xq', '')
            if concept_code and concept_name:
                res['ucx'] = self.update_concept(symbol, concept_code, concept_name, 'XQ', '', k_list_xq, c_list_xq)
        return res

    def update_by_em(self, symbol, info, k_list_em, c_list_em, t_em):
        """从东财中拉取数据进行更新"""
        res = {}
        # 改为只更新一次 - 毕竟不常用
        if k_list_em and c_list_em and t_em:
            return res
        sdb = GPLSymbolModel()
        tdb = GPLSymbolTextModel()
        code = info['code']
        # 概念板块
        ci_info = self.formatter.em.get_concept_info(code)
        if ci_info:
            concept_list = []
            for c in ci_info:
                concept_code = Attr.get(c, 'NEW_BOARD_CODE', '')
                concept_name = Attr.get(c, 'BOARD_NAME', '')
                des = Attr.get(c, 'BOARD_TYPE', '')
                if concept_code and concept_name:
                    res['uce'] = self.update_concept(symbol, concept_code, concept_name, 'EM', des, k_list_em, c_list_em)
                    if '昨日' not in concept_name:
                        concept_list.append(concept_name)
            concept_list = ','.join(concept_list)
            if concept_list and info['concept_list'] != concept_list:
                ext = {'update_list': info['update_list'] | {'em': Time.date()}} | {"concept_list": concept_list}
                res['use'] = sdb.update_symbol(symbol, {}, {}, ext)
        # 核心题材
        ct_list = self.formatter.em.get_concept_text(code)
        if ct_list:
            biz_code = 'EM_TC'
            t_list = t_em
            t_list = {f"{d['e_key']}": d for d in t_list}
            ct_info = Attr.group_item_by_key(ct_list, 'KEY_CLASSIF')
            for k, v in ct_info.items():
                c = v[0]
                title = Attr.get(c, 'KEY_CLASSIF', '')
                c_text = ''
                for vv in v:
                    kw = Attr.get(vv, 'KEYWORD', '')
                    text = Attr.get(vv, 'MAINPOINT_CONTENT', '')
                    c_text += "\r\n" if c_text else ""
                    c_text += text if title == kw else f"**{kw}**\r\n{text}\r\n"
                if title and c_text:
                    ek = Str.first_py_char(title)
                    d_info = Attr.get(t_list, ek, {})
                    if not d_info and not tdb.get_text(symbol, biz_code, ek):
                        res['ite'] = tdb.add_text({
                            "symbol": symbol,
                            "biz_code": biz_code,
                            "e_key": ek,
                            "e_des": title,
                            "e_val": c_text.strip(),
                        })
        return res

    def update_concept(self, symbol, code, name, type, des, k_list, c_list):
        """更新股票概念板块"""
        kdb = GPLConstKvModel()
        cdb = GPLConceptModel()
        biz_code = type + '_CONCEPT'
        k_info = Attr.get(k_list, code)
        c_list = {f"{d['concept_code']}": d for d in c_list}
        if not k_info and not kdb.get_const(biz_code, code):
            kdb.add_const({
                "biz_code": biz_code,
                "e_key": code,
                "e_des": des,
                "e_val": name,
            })
        c_info = Attr.get(c_list, code)
        if not c_info and not cdb.get_concept(symbol, type, code):
            cdb.add_concept({
                "symbol": symbol,
                "source_type": type,
                "concept_code": code,
                "concept_name": name,
            })
        return True

    def update_change_log(self, symbol, info):
        """更新股票变更日志"""
        ret = {}
        sdb = GPLSymbolModel()
        jdb = GPLSeasonModel()
        edb = GPLSymbolExtModel()
        s_biz_list = ['EM_GD_TOP10', 'EM_GD_TOP10_FREE']
        e_biz_list = ['EM_GD_NUM', 'EM_GD_ORG_T', 'EM_GD_ORG_D', 'EM_GD_ORG_L']
        for biz_code in s_biz_list:
            key = 'gd_top10_list' if 'EM_GD_TOP10' == biz_code else 'gd_top10_free_list'
            g_info = jdb.get_season_recent(symbol, biz_code, key)
            if not g_info:
                logger.debug(f"暂无股票季度数据<{symbol}><{biz_code} / {key}>", 'UP_EGD_SKP')
                continue
            gd_list = ','.join([f"{b['gd_name']}:{b['rate']}%" for b in g_info['e_val']])
            if gd_list and info[key] != gd_list:
                after = {key: gd_list}
                before = {key: info[key]} if info[key] else {}
                ext = {'update_list': info['update_list'] | {'gd': Time.date()}}
                ret['ugd'] = sdb.update_symbol(symbol, after, before, ext)
        for biz_code in e_biz_list:
            key = biz_code.lower()
            g_info = jdb.get_season_recent(symbol, biz_code, key)
            if not g_info:
                logger.debug(f"暂无股票季度数据<{symbol}><{biz_code} / {key}>", 'UP_EGE_SKP')
                continue
            e_info = edb.get_ext(symbol, biz_code, key)
            if not e_info:
                insert = {
                    "symbol": symbol,
                    "biz_code": biz_code,
                    "e_key": g_info.get('e_key', ''),
                    "e_des": g_info.get('e_des', ''),
                    "e_val": g_info.get('e_val', ''),
                    "sid": g_info.get('id', 0),
                    "std": g_info.get('season_date', Time.date('%Y-%m-%d')),
                }
                ret['ige'] = edb.add_ext(insert)
            else:
                if g_info['e_val'] != e_info['e_val']:
                    after = {key: g_info['e_val']}
                    before = {key: e_info['e_val']}
                    ret['uge'] = edb.update_ext(e_info['id'], symbol, key, after, before)
        return ret

