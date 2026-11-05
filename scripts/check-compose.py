"""Start an isolated Lab 2 stack, check SQL/HTTP/network isolation, then clean up."""

import json
import os
import socket
import subprocess
import uuid
from pathlib import Path
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]


def free_port():
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


def main():
    # Only this newly created project can be removed in the finally block.
    project = "bpta-delivery-check-" + uuid.uuid4().hex[:10]
    env = dict(os.environ, APP_PORT=str(free_port()), WEB_PORT=str(free_port()))
    env.pop("POSTGRES_PASSWORD", None)
    compose = [
        "docker",
        "compose",
        "--project-name",
        project,
        "--env-file",
        os.devnull,
        "-f",
        "compose.dev.yml",
    ]

    def run(*args, **kwargs):
        return subprocess.run(
            [*compose, *args], cwd=ROOT, env=env, check=True, **kwargs
        )

    # Ignore any personal .env: reproduce a fresh checkout with no credentials.
    # Validate both entrypoints and Compose's unset/empty/override semantics.
    for filename in ("compose.dev.yml", "compose.yml"):
        for password in (None, "", "delivery-check-override"):
            config_env = dict(env)
            if password is not None:
                config_env["POSTGRES_PASSWORD"] = password
            result = subprocess.run(
                [*compose[:-1], filename, "config", "--format", "json"],
                cwd=ROOT,
                env=config_env,
                check=True,
                capture_output=True,
                text=True,
            )
            config = json.loads(result.stdout)
            assert config["services"]["db"]["environment"]["POSTGRES_PASSWORD"] == (
                password or "local-dev-change-me"
            ), (filename, "database password interpolation")

    try:
        run("config", "--quiet")
        run("up", "-d", "--build", "--wait", "--wait-timeout", "180")
        run(
            "exec",
            "-T",
            "db",
            "psql",
            "-U",
            "bpta",
            "-d",
            "bpta",
            "-v",
            "ON_ERROR_STOP=1",
            input=(ROOT / "database/check-schema.sql").read_bytes(),
        )
        with urlopen(
            f"http://127.0.0.1:{env['APP_PORT']}/health", timeout=10
        ) as response:
            assert json.load(response) == {"status": "ok", "service": "bpta-app-stub"}
        with urlopen(f"http://127.0.0.1:{env['WEB_PORT']}/", timeout=10) as response:
            assert "БПТА" in response.read().decode("utf-8")
        run(
            "exec",
            "-T",
            "app",
            "python",
            "-c",
            "import urllib.request; assert urllib.request.urlopen('http://ai-service:8000/health').status == 200",
        )
        run(
            "exec",
            "-T",
            "agent",
            "python",
            "-c",
            "import socket\ntry:\n socket.getaddrinfo('db',5432)\nexcept socket.gaierror:\n print('PASS: agent cannot resolve db')\nelse:\n raise SystemExit('FAIL: agent resolves db')",
        )
        print(
            "PASS: Compose health, 10 SQL checks, HTTP, AI alias, DB network isolation"
        )
    finally:
        # Unique project and its throwaway volume were created by this invocation only.
        run("down", "--volumes", "--remove-orphans")


if __name__ == "__main__":
    main()
