"""Error types mapped to stable CLI exit codes (spec FR-09)."""


class TodoError(Exception):
    code = "ERROR"
    exit_code = 1


class ValidationError(TodoError):
    code = "VALIDATION_ERROR"
    exit_code = 1


class NotFoundError(TodoError):
    code = "NOT_FOUND"
    exit_code = 2


class TransitionError(TodoError):
    code = "INVALID_TRANSITION"
    exit_code = 3


class StorageError(TodoError):
    code = "STORAGE_ERROR"
    exit_code = 4
