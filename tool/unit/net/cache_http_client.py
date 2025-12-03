from tool.core import Http, Attr, Str, Ins
from tool.db.cache.redis_client import RedisClient


class CacheHttpClient:

    @staticmethod
    def batch_request(r_list, success=None):
        """
        批量进行网络请求并对其结果缓存
          - [!] 注意不要嵌套多线程；一般是放在初始化的程序中执行，确保外面同一时间只有一个线程在调用
          - 推荐使用延迟任务进行调用，因为这个方法很耗时
          - 每个链接的缓存键为：u_key = Str.md5(f"{url}--{params}")

        :param r_list: 请求参数列表 - [{"method":"GET", "url":"xxx", "params":{}, "headers": {}}]
        :param success: 成功标志 - {"key": "code", "val": "200", "hpk": "data.0.name"}
        :return: 成功缓存的个数
        """
        r_list = Attr.chunk_list(r_list, 100)  # 对列表进行分块

        # 分块处理方法
        def _chunk_request(par):
            proxy_list = []
            redis = RedisClient()
            if not len(par):
                return False
            # 批量获取代理链接
            ul = 100 if len(par) >= 100 else len(par)  # 最多100个，这是代理的限制
            pn = Attr.random_choice([51, 82, 57, 61])  # 从四个最大的池中随机获取，其他池数量不够
            p_list, pf = Http.get_proxy(ul, pn)
            if not pf:
                raise Exception(f"Get http proxy list failed")

            # 以代理数量为准进行参数整合
            for i, p in enumerate(p_list):
                proxy = {
                    "i": i,
                    "pn": pn,
                    "proxy": p,
                } | par[i]
                proxy_list.append(proxy)

            # 多个线程一起执行，加快缓存速度
            @Ins.multiple_executor(8)
            def _cache_req(p)->dict | bool:
                is_cache = False
                cache_key = 'NET_BATCH_REQ'
                u_key = Str.md5(f"{p['url']}--{p['params']}")  # 请求的唯一标识
                if redis.get(cache_key, [u_key]):  # 如果已经存在了就没必要继续请求了
                    return False
                res = Http.send_request(p['method'], p['url'], p['params'], p['headers'], p['proxy'])
                if not res:
                    is_cache = False
                if success:
                    if success.get("hpk"):
                        if Attr.get_by_point(res, success.get("hpk")):
                            is_cache = True
                    elif success.get("key"):
                        if res.get(success.get("key")) == success.get("val"):
                            is_cache = True
                else:
                    is_cache = True
                if is_cache:
                    ret = {"args": p, "data": res}
                    redis.set(cache_key, ret, [u_key])  # 缓存请求结果
                return is_cache

            res = _cache_req(proxy_list)  # 批量执行 - {md5xx1": False, "md5xx2": True}
            return sum(int(v) for v in res.values())  # 返回成功个数

        return sum([_chunk_request(r) for r in r_list])  # 返回成功缓存的个数
