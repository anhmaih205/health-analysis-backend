class AppException(Exception):
    """
    最小可用业务异常
    """

    def __init__(
        self,
        code: str,
        message: str,
        http_status: int = 400
    ):
        self.code = code
        self.message = message
        self.http_status = http_status
        super().__init__(message)

    def to_dict(self):
        return {
            "status": "error",
            "code": self.code,
            "message": self.message
        }
