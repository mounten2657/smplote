from tool.core.attr import Attr


class Api:
    @staticmethod
    def restful(data, msg, code):
        if Attr.has_keys(data, ['code', 'data', 'msg']):
            return data
        return {"code": code, "msg": msg, "data": Attr.parse_json_ignore(data)}

    @staticmethod
    def success(data, msg='success', code=0):
        return Api.restful(data, msg, code)

    @staticmethod
    def error(msg='error', data=None, code=999):
        return Api.restful(data, msg, code)


