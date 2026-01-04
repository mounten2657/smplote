from service.gpl.gpl_formatter_service import GplFormatterService
from service.gpl.gpl_update_ecc_service import GPLUpdateEccService
from service.gpl.gpl_update_edv_service import GPLUpdateEdvService
from service.gpl.gpl_update_efn_service import GPLUpdateEfnService
from service.gpl.gpl_update_egd_service import GPLUpdateEgdService
from model.gpl.gpl_symbol_model import GPLSymbolModel
from model.gpl.gpl_const_kv_model import GPLConstKvModel
from model.gpl.gpl_concept_model import GPLConceptModel
from model.gpl.gpl_symbol_text_model import GPLSymbolTextModel
from model.gpl.gpl_season_model import GPLSeasonModel
from tool.core import Ins, Logger, Str, Time, Attr

logger = Logger()


@Ins.singleton
class GPLUpdateExtService:
    """股票更新附属类"""

    # 初始化的开始结束日期
    _INIT_ST = GplFormatterService.INIT_ST
    _INIT_ET = GplFormatterService.INIT_ET

    # 无法正常获取股东信息的股票列表
    _S_GD_LIST = [
        "SH688755","SH603382","SZ301590","SH603014","SZ301636","SZ301662","SZ301678","SH688729","SZ301630","SH603262",
        "BJ920027", "BJ920037", "BJ920068", "BJ920108", "SH600930","SZ001400", "SZ301609"
    ]

    def __init__(self):
        self.formatter = GplFormatterService()
        self.ecc = GPLUpdateEccService()
        self.edv = GPLUpdateEdvService()
        self.efn = GPLUpdateEfnService()
        self.egd = GPLUpdateEgdService()

    def update_symbol_ext(self, code_str, is_force=0, current_date=None):
        """更新股票额外数据 - 多线程"""
        code_list = [Str.remove_stock_prefix(c) for c in code_str.split(',') if c.strip()]
        if not code_list:
            return False

        # 初始化数据库实例
        sdb = GPLSymbolModel()
        jdb = GPLSeasonModel()
        kdb = GPLConstKvModel()
        cdb = GPLConceptModel()
        tdb = GPLSymbolTextModel()

        # 获取基础数据
        all_code_list = self.formatter.get_stock_code_all()
        symbol_list = [Str.add_stock_prefix(c) for c in code_list]
        s_list = {d["symbol"]: d for d in sdb.get_symbol_list(symbol_list)}

        # 计算通用时间参数
        debug = False if current_date != Time.date('%Y-%m-%d') else True  # 调试模式 - 线上默认今日日期一定是 False
        current_date = current_date if current_date else Time.date('%Y-%m-%d')
        current_day = int(current_date[-2:])
        is_all = int(is_force > (900 if debug else 90))
        n = 103 if is_all else 3
        td = self._INIT_ET if is_all else current_date
        sd = self._INIT_ST if is_all else Time.dnd(td, 0 - (120 if debug else 30))
        day_list = list(reversed([Time.recent_season_day(nn) for nn in range(1, n + 1)]))
        cdl = [Time.date('%Y-%m-01'), Time.date('%Y-%m-10'), Time.date('%Y-%m-20')]
        nrd_list = range(1, 32)

        # 数据查询配置 - （key: 业务标识, value: (force条件, 执行日期, 业务代码, 参数列表)）
        season_data_config = {
            # 普通规则 - 日期交叉执行
            "gd": (lambda f: f in (0, 91), [3, 13], "EM_GD_TOP10", [day_list, '']),
            "gd_free": (lambda f: f in (0, 91), [3, 13], "EM_GD_TOP10_FREE", [day_list, '']),
            "gdn": (lambda f: f in (0, 92), [4, 14], "EM_GD_NUM", [day_list, '']),
            "gdt": (lambda f: f in (0, 93), [5, 15], "EM_GD_ORG_T", [day_list, '']),
            "gdd": (lambda f: f in (0, 94), [6, 16], "EM_GD_ORG_D", [day_list, '']),
            "gdl": (lambda f: f in (0, 95), [7, 17], "EM_GD_ORG_L", [day_list, '']),
            "dvo": (lambda f: f in (0, 96), [8, 18], "EM_DV_OV", [cdl, '']),
            "dvt": (lambda f: f in (0, 96), [8, 18], "EM_DV_OV_TEXT", [cdl, '']),
            "dvh": (lambda f: f in (0, 97), [9, 19], "EM_DV_HIST", [[], sd]),
            "dvr": (lambda f: f in (0, 98), [10, 20], "EM_DV_HIST_R", [[], sd]),
            "dvp": (lambda f: f in (0, 99), [11, 21], "EM_DV_HIST_P", [[], sd]),
            "zyi": (lambda f: f in (0, 100), [12, 22], "EM_ZY_IT", [[], sd]),
            "fni": (lambda f: f in (0, 101), [13, 23], "EM_FN_IT", [[], sd]),
            "fnd": (lambda f: f in (0, 102), [14, 24], "EM_FN_DP", [[], sd]),
            "fnn": (lambda f: f in (0, 103), [15, 25], "EM_FN_NF", [[], sd]),
            "sfn": (lambda f: f in (0, 104), [16, 26], "EM_FN_NF", [[], sd]),
            "dfn": (lambda f: f in (0, 105), [17, 27], "EM_FN_NF", [[], sd]),
            # 特殊规则 - 文本类、一次性等
            "zyb": (lambda f: f == 200, nrd_list, "EM_ZY_BA", symbol_list),
            "cem": (lambda f: f == 201, nrd_list, "EM_CONCEPT", symbol_list),
            "cxq": (lambda f: f == 202, nrd_list, "XQ_CONCEPT", symbol_list),
        }

        # 批量查询集成数据
        season_data = {}
        for key, (force_check, rd_list, biz_code, query_param) in season_data_config.items():
            rd_list = list(range(32)) if debug else rd_list
            if force_check(is_force) and current_day in rd_list:
                if key == "zyb":
                    season_data[key] = Attr.group_item_by_key(tdb.get_text_list(query_param, biz_code), "symbol")
                elif key == "cem":
                    season_data[key]["k_list_em"] = kdb.get_const_list("EM_CONCEPT")
                    season_data[key]["c_list_em"] = Attr.group_item_by_key(cdb.get_concept_list(symbol_list, "EM"), "symbol")
                    season_data[key]["t_list_em"] = Attr.group_item_by_key(tdb.get_text_list(symbol_list, "EM_TC"), "symbol")
                elif key == "cxq":
                    season_data[key]["k_list_xq"] = kdb.get_const_list("XQ_CONCEPT")
                    season_data[key]["c_list_xq"] = Attr.group_item_by_key(cdb.get_concept_list(symbol_list, "XQ"), "symbol")
                else:  # 通用季度数据查询
                    season_data[key] = jdb.get_season_list(symbol_list, query_param[0], biz_code, query_param[1])
        # 加载固定执行且不需要原始数据的
        season_data['scl'] = None

        @Ins.multiple_executor(2)
        def _up_ext_exec(code):
            Time.sleep(Str.randint(1, 10) / 100)
            ret = {}
            symbol = Str.add_stock_prefix(code)
            info = s_list.get(symbol)
            percent = self.formatter.get_percent(code, code_list, all_code_list)

            # 参数检查
            if not info:
                logger.warning(f"未查询到股票数据<{symbol}>{percent}", 'UP_EXT_WAR')
                return False
            logger.debug(f"更新股票额外数据<{symbol}>{percent} - STA", 'UP_EXT_INF')

            # 特殊参数
            is_special = int(symbol in self._S_GD_LIST)
            sd_list = [current_date if not is_force else self._INIT_ET] if is_special else day_list
            k_list_em = Attr.get_by_point(season_data, f"cem.k_list_em", [])
            cl_em = Attr.get_by_point(season_data, f"cem.c_list_em.{symbol}", [])
            t_em = Attr.get_by_point(season_data, f"cem.t_list_em.{symbol}", [])
            k_list_xq = Attr.get_by_point(season_data, f"cxq.k_list_xq", [])
            cl_xq = Attr.get_by_point(season_data, f"cxq.c_list_xq.{symbol}", [])
            is_scl = any('gd' in key for key in season_data.keys())

            # 数据更新逻辑（key: 业务标识, value: (更新方法, 日志说明, 日志标识, 额外参数)）
            season_update_config = {
                # 普通规则 - 条件执行
                "gd": (self.egd.up_gd_em, "十大股东", "GDA", (season_data.get('gd_free'), sd_list, n, is_special)),
                "gdn": (self.egd.up_gdn_em, "股东人数合计", "GDN", (sd_list, n, is_special)),
                "gdt": (self.egd.up_gdt_em, "股东机构合计", "GDT", (day_list,)),
                "gdd": (self.egd.up_gdd_em, "股东机构明细", "GDD", (day_list,)),
                "gdl": (self.egd.up_gdl_em, "股东机构列表", "GDL", (day_list,)),
                "dvo": (self.edv.up_dvo_em, "分红概览", "DVO", (season_data.get('dvt'), td,)),
                "dvh": (self.edv.up_dvh_em, "分红历史", "DVH", (td, n,)),
                "dvr": (self.edv.up_dvr_em, "分红股息率", "DVR", (sd, td,)),  # 1000w
                "dvp": (self.edv.up_dvp_em, "分红股利支付率", "DVP", (sd, td,)),
                "zyi": (self.edv.up_zyi_em, "主营构成列表", "ZYI", (is_all,)),
                "fni": (self.efn.up_fni_em, "财务主要指标", "FNI", (td, n,)),
                "fnd": (self.efn.up_fnd_em, "财务杜邦分析", "FND", (td, n,)),
                "fnn": (self.efn.up_fnn_em, "财务公告文件", "FNN", (td, n,)),
                "sfn": (self.efn.save_fnn_em_txt, "保存财务公告文本", "SFN", (td, sd,)),
                "dfn": (self.efn.download_fnn_em, "下载财务公告文件", "DFN", (td, sd, info,)),
                # 特殊规则 - 一次性 或 固定执行
                "zyb": (self.edv.up_zyb_em, "经营评述长文本", "ZYB", (Attr.get_by_point(season_data, f"zyb.{symbol}"),)),
                "cem": (self.ecc.update_by_em, "东财概念", "CEM", (info, k_list_em, cl_em, t_em,)),
                "cxq": (self.ecc.update_by_xq, "雪球概念", "CXQ", (info, k_list_xq, cl_xq,)),
                "scl": (self.ecc.update_change_log, "股票变更", "SCL", (info, is_scl)),
            }

            # 批量执行数据更新
            for key, (update_func, log_txt, log_tag, extra_args) in season_update_config.items():
                if key in season_data:  # 只更新已查询到数据的业务
                    update_ret = update_func(symbol, *(season_data[key],) if season_data[key] is not None else (), *extra_args)
                    ret |= update_ret
                    logger.debug(f"更新{log_txt}结果<{symbol}>{percent} - {log_tag} - {ret}", 'UP_EXT_RET')

            return ret

        # return {code: _up_ext_exec(code) for code in code_list}  # 单线程，调试专用，注释装饰器
        return _up_ext_exec(code_list)  # 多线程
