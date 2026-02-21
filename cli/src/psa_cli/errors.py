from __future__ import annotations

from enum import IntEnum
from typing import Any


class ExitCode(IntEnum):
    OK = 0
    INTERNAL = 1
    ARGUMENTS = 2
    IO_OR_JSON = 3
    VALIDATION = 4


class CliError(RuntimeError):
    exit_code: ExitCode = ExitCode.INTERNAL
    error_code: str = "internal_error"

    def __init__(self, message: str, *, details: Any = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details


class CliIoError(CliError):
    exit_code = ExitCode.IO_OR_JSON
    error_code = "io_error"


class CliValidationError(CliError):
    exit_code = ExitCode.VALIDATION
    error_code = "validation_error"


class CliArgumentError(CliError):
    exit_code = ExitCode.ARGUMENTS
    error_code = "invalid_arguments"


class CliDomainError(CliError):
    exit_code = ExitCode.VALIDATION

    def __init__(self, error_code: str, message: str, *, details: Any = None) -> None:
        super().__init__(message, details=details)
        self.error_code = error_code
