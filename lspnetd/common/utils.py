import os
import socket
import subprocess
from lspnetd.common.logger import get_logger


logger = get_logger("utils")


def ns_wrap(namespace: str, args: list[str]):
    if namespace:
        return ["ip", "netns", "exec", namespace] + args
    return args


def sudo_wrap(args: list[str]):
    if os.geteuid() != 0:
        logger.warning('sudo: {}'.format(args))
        return ["sudo"] + args
    return args


def sudo_call(args: list[str]):
    return subprocess.check_call(sudo_wrap(args))


def sudo_call_output(args: list[str]):
    return subprocess.check_output(sudo_wrap(args), encoding='utf-8')


def hostport_resolve(name: str):
    if "[" in name and "]" in name:
        # [ipv6]:port
        parts = name.split(']')
        if len(parts) < 2:
            return parts[0][1:], 0

        assert len(parts) == 2, "Invalid hostport format, detected invalid [ipv6]:port"
        return parts[0][1:], int(parts[1])

    parts = name.split(':')
    if len(parts) < 2:
        real_host = socket.gethostbyname(parts[0])
        return real_host, 0
    
    assert(len(parts) == 2), "Invalid hostport format, detected invalid host:port or ipv4:port"
    
    real_host = socket.gethostbyname(parts[0])
    return real_host, int(parts[1])


def human_readable_bytes(b: int):
    if b < 1024:
        return "{} B".format(b)
    if b < 1024 * 1024:
        return "{:.2f} KiB".format(b / 1024)
    if b < 1024 * 1024 * 1024:
        return "{:.2f} MiB".format(b / 1024 / 1024)

    return "{:.2f} GiB".format(b / 1024 / 1024 / 1024)


def human_readable_duration(s: int):
    if s < 60:
        return "{}s".format(s)
    if s < 60 * 60:
        return "{}m{}s".format(int(s / 60), s % 60)

    return "{}h{}m{}s".format(int(s / 3600), int((s % 3600) / 60), s % 60)


def get_tempdir_path(namespace: str):
    return "/tmp/networktools-{}".format(namespace)
