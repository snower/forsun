# -*- coding: utf-8 -*-
# 18/1/23
# create by: snower

from .servers.processor.ttypes import ForsunPlanError

class ActionExecuteRetry(Exception):
    def __init__(self):
        pass

class UnknownError(ForsunPlanError):
    def __init__(self):
        super(UnknownError, self).__init__(1001, u"未知错误")

    def __hash__(self):
        return id(self)

class WillNeverArriveTimeError(ForsunPlanError):
    def __init__(self):
        super(WillNeverArriveTimeError, self).__init__(1002, u"定时时间错误")

    def __hash__(self):
        return id(self)

class NotFoundPlanError(ForsunPlanError):
    def __init__(self):
        super(NotFoundPlanError, self).__init__(1003, u"计划未找到")

    def __hash__(self):
        return id(self)

class StorePlanError(ForsunPlanError):
    def __init__(self):
        super(StorePlanError, self).__init__(1004, u"保存计划错误")

    def __hash__(self):
        return id(self)

class RemovePlanError(ForsunPlanError):
    def __init__(self):
        super(RemovePlanError, self).__init__(1005, u"移除计划错误")

    def __hash__(self):
        return id(self)

class UnknownActionError(ForsunPlanError):
    def __init__(self):
        super(UnknownActionError, self).__init__(1006, u"未知处理动作类型")

    def __hash__(self):
        return id(self)

class RequiredArgumentError(ForsunPlanError):
    def __init__(self, argument):
        super(RequiredArgumentError, self).__init__(1007, u"%s参数是必须的" % argument)

    def __hash__(self):
        return id(self)