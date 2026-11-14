"""Secret-mounted backend transformation entry point. Never print input or errors."""

import os
import sys
from typing import Literal

try:
    from .backend_config import process_backend_config_content
except ImportError:  # The container executes this entry point as a script.
    from backend_config import (  # type: ignore[no-redef,import-not-found]
        process_backend_config_content,
    )


def main() -> int:
    try:
        syntax, source, destination = sys.argv[1:]
        format: Literal["yaml", "hcl"]
        if syntax == "yaml":
            format = "yaml"
        elif syntax == "hcl":
            format = "hcl"
        else:
            raise ValueError("Invalid backend format")
        with open(source, encoding="utf-8") as stream:
            content, _ = process_backend_config_content(stream.read(), format)
        fd = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(content)
        return 0
    except Exception:
        sys.stderr.write("Backend configuration validation/conversion failed\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
