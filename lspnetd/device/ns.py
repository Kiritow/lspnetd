from lspnetd.common.utils import sudo_call


def list_raw_netns_paths():
    with open("/proc/mounts", "r") as f:
        lines = f.read().splitlines()
        mounts = [line.split() for line in lines if line.startswith("nsfs")]
        return list(set([mount[1] for mount in mounts]))


def ensure_netns(namespace: str):
    if not namespace:
        return

    netns_paths = list_raw_netns_paths()
    if f"/run/netns/{namespace}" in netns_paths or f"/var/run/netns/{namespace}" in netns_paths:
        return

    sudo_call(["ip", "netns", "add", namespace])
