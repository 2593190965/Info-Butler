class AppError(Exception):
    def __init__(self, message: str, code: int = 500, detail: str | None = None):
        self.message = message
        self.code = code
        self.detail = detail or message
        super().__init__(self.message)


class NotFoundError(AppError):
    def __init__(self, resource: str, id_value: str | int):
        super().__init__(
            message=f"{resource} not found",
            code=404,
            detail=f"{resource} with id '{id_value}' not found",
        )


class ValidationError(AppError):
    def __init__(self, message: str):
        super().__init__(message=message, code=422)


class ExternalServiceError(AppError):
    def __init__(self, service: str, detail: str):
        super().__init__(
            message=f"{service} service error",
            code=502,
            detail=f"{service}: {detail}",
        )
