from __future__ import annotations

import fcntl
import os
import time
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from psa_cli.errors import CliDomainError

LOCK_TIMEOUT_SECONDS = 5.0
LOCK_POLL_INTERVAL_SECONDS = 0.05


@contextmanager
def exclusive_lock(
    lock_path: Path, *, timeout_seconds: float = LOCK_TIMEOUT_SECONDS
) -> Iterator[None]:
    fd: int | None = None
    try:
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(lock_path, os.O_CREAT | os.O_RDWR, 0o600)
    except OSError as exc:
        raise CliDomainError(
            "storage_error",
            f"failed to initialize lock {lock_path}",
            details={"lock_path": str(lock_path), "reason": exc.strerror or str(exc)},
        ) from exc

    start = time.monotonic()
    acquired = False
    try:
        while True:
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                acquired = True
                break
            except BlockingIOError:
                if time.monotonic() - start >= timeout_seconds:
                    raise CliDomainError(
                        "lock_timeout",
                        f"failed to acquire lock for {lock_path}",
                        details={"lock_path": str(lock_path)},
                    ) from None
                time.sleep(LOCK_POLL_INTERVAL_SECONDS)
        yield
    finally:
        if acquired and fd is not None:
            fcntl.flock(fd, fcntl.LOCK_UN)
        if fd is not None:
            os.close(fd)
