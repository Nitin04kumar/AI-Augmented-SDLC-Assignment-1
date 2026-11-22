class TodoError(Exception):
    def __init__(self, code: str, message: str, exit_code: int) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.exit_code = exit_code

    def payload(self) -> dict:
        return {"error": {"code": self.code, "message": self.message}}


class ValidationError(TodoError):
    def __init__(self, message: str) -> None:
        super().__init__("VALIDATION_ERROR", message, 1)


class NotFoundError(TodoError):
    def __init__(self, task_id: int) -> None:
        super().__init__("NOT_FOUND", f"Task {task_id} not found", 2)


class InvalidTransitionError(TodoError):
    def __init__(self, current: str, target: str) -> None:
        super().__init__(
            "INVALID_TRANSITION",
            f"Invalid status transition from {current} to {target}",
            3,
        )


class StorageError(TodoError):
    def __init__(self, message: str) -> None:
        super().__init__("STORAGE_ERROR", message, 4)
