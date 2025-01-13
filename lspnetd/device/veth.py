from lspnetd.common.utils import ns_wrap, sudo_call


def create_veth_device(ns1: str, name1: str, addr1: str, ns2: str, name2: str, addr2: str, up: bool = True):
    call_args: list[str] = ["ip", "link", "add", name1]
    if ns1:
        call_args += ["netns", ns1]
    call_args += ["type", "veth", "peer", name2]
    if ns2:
        call_args += ["netns", ns2]
    
    sudo_call(call_args)
    sudo_call(ns_wrap(ns1, ["ip", "address", "add", "dev", name1, addr1]))
    sudo_call(ns_wrap(ns2, ["ip", "address", "add", "dev", name2, addr2]))

    if up:
        sudo_call(ns_wrap(ns1, ["ip", "link", "set", "dev", name1, "up"]))
        sudo_call(ns_wrap(ns2, ["ip", "link", "set", "dev", name2, "up"]))
