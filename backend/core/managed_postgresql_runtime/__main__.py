"""Module entry point that prevents dotenv configuration from overriding input."""

import os

from .entrypoint import configure_runtime_environment


configure_runtime_environment(os.environ)

from .cli import main


raise SystemExit(main())
