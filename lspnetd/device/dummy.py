from lspnetd.common.utils import sudo_call


def create_dummy_device(name: str, address: str, mtu: int, up: bool = True):
    sudo_call(["ip", "link", "add", name, "type", "dummy"])
    sudo_call(["ip", "address", "add", "dev", name, address])
    sudo_call(["ip", "link", "set", "dev", name, "mtu", str(mtu)])
    if up:
        sudo_call(["ip", "link", "set", "dev", name, "up"])
