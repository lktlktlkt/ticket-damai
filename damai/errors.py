class PerformanceError(Exception):
    pass


class NotElementError(PerformanceError):
    pass


class LoginError(PerformanceError):
    pass


class CongestionError(PerformanceError):
    pass
