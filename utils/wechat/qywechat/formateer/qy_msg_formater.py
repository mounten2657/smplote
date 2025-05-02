

class QyMsgFormatter(object):
    """企业微信应用消息回调结构体"""
    msg_id = None
    create_time = None

    ctype = None
    content = None

    from_user_id = None
    from_user_nickname = None
    to_user_id = None
    to_user_nickname = None
    other_user_id = None
    other_user_nickname = None
    my_msg = False
    self_display_name = None

    is_group = False
    is_at = False
    actual_user_id = None
    actual_user_nickname = None
    at_list = None

    _prepare_fn = None
    _prepared = False
    _rawmsg = None

    def __init__(self, _rawmsg):
        self._rawmsg = _rawmsg

    def prepare(self):
        if self._prepare_fn and not self._prepared:
            self._prepared = True
            self._prepare_fn()

    def __str__(self):
        return ("ChatMessage: id={}, create_time={}, ctype={}, content={}, from_user_id={}, from_user_nickname={}, "
                "to_user_id={}, to_user_nickname={}, other_user_id={}, other_user_nickname={}, is_group={}, is_at={}, "
                "actual_user_id={}, actual_user_nickname={}, at_list={}").format(
            self.msg_id,
            self.create_time,
            self.ctype,
            self.content,
            self.from_user_id,
            self.from_user_nickname,
            self.to_user_id,
            self.to_user_nickname,
            self.other_user_id,
            self.other_user_nickname,
            self.is_group,
            self.is_at,
            self.actual_user_id,
            self.actual_user_nickname,
            self.at_list
        )
