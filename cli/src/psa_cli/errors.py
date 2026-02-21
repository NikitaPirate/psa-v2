from __future__ import annotations

from enum import IntEnum


class ExitCode(IntEnum):
    OK = 0
    INTERNAL = 1
    ARGUMENTS = 2
    RUNTIME = 3
    VALIDATION = 4
    STATE = 5


class CliError(RuntimeError):
    exit_code: ExitCode = ExitCode.INTERNAL
    error_code: str = "internal_error"

    def __init__(self, message: str, *, error_code: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        if error_code is not None:
            self.error_code = error_code


class CliArgumentsError(CliError):
    exit_code = ExitCode.ARGUMENTS
    error_code = "arguments_error"


class CliRuntimeError(CliError):
    exit_code = ExitCode.RUNTIME
    error_code = "runtime_error"


class CliValidationError(CliError):
    exit_code = ExitCode.VALIDATION
    error_code = "validation_error"


class CliStateError(CliError):
    exit_code = ExitCode.STATE
    error_code = "state_error"


class CliInternalError(CliError):
    exit_code = ExitCode.INTERNAL
    error_code = "internal_error"
