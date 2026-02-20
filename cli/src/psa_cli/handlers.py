from __future__ import annotations

from typing import Any

from psa_cli.commands_create import execute_create
from psa_cli.commands_evaluate import execute_evaluate
from psa_cli.commands_show import execute_show
from psa_cli.commands_update import execute_update
from psa_cli.errors import CliValidationError
from psa_cli.store import MemoryStore


def execute(args: Any, store: MemoryStore) -> dict[str, Any]:
    if args.group == "show":
        return execute_show(args, store)
    if args.group == "create":
        return execute_create(args, store)
    if args.group == "update":
        return execute_update(args, store)
    if args.group == "evaluate":
        return execute_evaluate(args, store)

    raise CliValidationError(
        f"unsupported command group: {args.group}",
        error_code="unsupported_group",
    )
