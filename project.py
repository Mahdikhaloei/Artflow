#! /usr/bin/env python3

import argparse
import os
import shlex
import sys

PROJECT_ROOT = os.path.dirname(os.path.realpath(__file__))
PROJECT_NAME = "artflow"
LOCAL_ENV_FILE = f"{PROJECT_ROOT}/.envs/.local/.artflow"
LOCAL_ENV_TEMPLATE = (
    "# This file contains environment variables local to this setup.\n"
    "# You can also use it to overwrite environment variables only on your machine.\n\n"
)


def parse_args(arguments):
    parser = argparse.ArgumentParser(
        prog="project.py",
        description="Helper script to simplify the docker workflow."
    )
    subparsers = parser.add_subparsers(dest="command")

    run_parser = subparsers.add_parser("start", help="Start the Flask App containers.")
    run_parser.add_argument("-d", "--deamon-mode", help="Run containers in background", action="store_true")
    run_parser.add_argument("-b", "--build", help="Rebuild image before running", action="store_true")

    subparsers.add_parser("stop", help="Stop the running containers.")

    restart_parser = subparsers.add_parser("restart", help="Restart containers.")
    restart_parser.add_argument("action", nargs=argparse.REMAINDER)

    logs_parser = subparsers.add_parser("logs", help="Show logs.")
    logs_parser.add_argument("-f", "--follow-logs", help="Follow logs", action="store_true")

    subparsers.add_parser("shell", help="Open bash shell inside container.")

    exec_parser = subparsers.add_parser("exec", help="Execute command inside container.")
    exec_parser.add_argument("action", nargs=argparse.REMAINDER)

    setup_parser = subparsers.add_parser("setup", help="Initialize local environment.")
    setup_parser.add_argument("-f", "--force", help="Force overwrite", action="store_true")

    test_parser = subparsers.add_parser("test", help="Run pytest tests inside container.")
    test_parser.add_argument("path", nargs="*", default=["core/tests/"], help="Test path(s) to run")

    run_parser.add_argument("-n", "--no-cache", help="Build images without cache", action="store_true")

    subparsers.add_parser("mypy", help="Run mypy static type checker.")

    args = parser.parse_args(arguments)

    if not args.command:
        parser.print_help()
        exit()
    return args


def get_docker_compose() -> str:
    return "docker-compose"


class Interpreter:
    docker_compose_command = get_docker_compose()

    @classmethod
    def interpret(cls, args: argparse.Namespace):
        method = getattr(cls, args.command.replace("-", "_"), None)
        if not method:
            raise NotImplementedError(f'The command "{args.command}" is not implemented.')
        method(args)

    @classmethod
    def setup(cls, args: argparse.Namespace | None = None):
        if (args and args.force) or not os.path.isfile(LOCAL_ENV_FILE):
            print(f"Setting up {LOCAL_ENV_FILE}...")
            with open(LOCAL_ENV_FILE, "w+") as f:
                f.write(LOCAL_ENV_TEMPLATE)

    @classmethod
    def start(cls, args: argparse.Namespace):
        if not os.path.isfile(LOCAL_ENV_FILE):
            cls.setup()

        if args.build:
            build_cmd = [cls.docker_compose_command, f"-p {shlex.quote(PROJECT_NAME)}", "-f local.yml", "build"]
            if args.no_cache:
                build_cmd.append("--no-cache")
            os.system(" ".join(build_cmd))

        up_cmd = [cls.docker_compose_command, f"-p {shlex.quote(PROJECT_NAME)}", "-f local.yml", "up"]
        if args.deamon_mode:
            up_cmd.append("-d")
        os.system(" ".join(up_cmd))

    @classmethod
    def stop(cls, args: argparse.Namespace):
        command = [cls.docker_compose_command, f"-p {shlex.quote(PROJECT_NAME)}", "-f local.yml", "down"]
        os.system(" ".join(command))

    @classmethod
    def restart(cls, args: argparse.Namespace):
        command = [
            cls.docker_compose_command,
            f"-p {shlex.quote(PROJECT_NAME)}",
            "-f local.yml",
            "restart",
            *args.action
        ]
        os.system(" ".join(command))

    @classmethod
    def logs(cls, args: argparse.Namespace):
        command = [cls.docker_compose_command, f"-p {shlex.quote(PROJECT_NAME)}", "-f local.yml", "logs"]
        if args.follow_logs:
            command.append("-f")
        os.system(" ".join(command))

    @classmethod
    def shell(cls, args: argparse.Namespace):
        command = [
            cls.docker_compose_command,
            f"-p {shlex.quote(PROJECT_NAME)}",
            "-f local.yml",
            "exec",
            "bash"
        ]
        os.system(" ".join(command))

    @classmethod
    def exec(cls, args: argparse.Namespace):
        command = [
            cls.docker_compose_command,
            f"-p {shlex.quote(PROJECT_NAME)}",
            "-f local.yml",
            "exec",
            *args.action
        ]
        os.system(" ".join(command))

    @classmethod
    def mypy(cls, args: argparse.Namespace):
        command = [
            cls.docker_compose_command,
            f"-p {shlex.quote(PROJECT_NAME)}",
            "-f local.yml",
            "exec",
            "-w /app/core", "-T", "artflow",
            "mypy", "--explicit-package-bases", ".", "--config-file=mypy.ini"
        ]
        os.system(" ".join(command))

    @classmethod
    def test(cls, args):
        if not os.path.isfile(LOCAL_ENV_FILE):
            cls.setup()

        test_paths = args.path or ["core/tests/"]
        test_paths_str = " ".join(shlex.quote(path) for path in test_paths)

        command = [
            cls.docker_compose_command,
            f"-p {shlex.quote(PROJECT_NAME)}",
            "-f local.yml",
            "exec",
            "artflow",
            "pytest",
            "--maxfail=1",
            "--disable-warnings",
            "-q",
            test_paths_str
        ]
        os.system(" ".join(command))


if __name__ == "__main__":
    arguments = parse_args(sys.argv[1:])
    Interpreter.interpret(arguments)
