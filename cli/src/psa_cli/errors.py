from __future__ import annotations

from enum import IntEnum


class ExitCode(IntEnum):
    OK = 0
    INTERNAL = 1
    ARGUMENTS = 2
    IO_OR_JSON = 3
    VALIDATION = 4


class CliError(RuntimeError):
    exit_code: ExitCode = ExitCode.INTERNAL

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class CliIoError(CliError):
    exit_code = ExitCode.IO_OR_JSON


class CliValidationError(CliError):
    exit_code = ExitCode.VALIDATION
