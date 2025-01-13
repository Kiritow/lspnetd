from dataclasses import dataclass


@dataclass
class ContainerBindMountStatus:
    source: str
    target: str
    flags: list[str]


@dataclass
class ContainerStatus:
    id: str
    bind_mounts: list[ContainerBindMountStatus]
