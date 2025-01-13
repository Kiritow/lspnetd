import json
from lspnetd.common.utils import ns_wrap, sudo_call_output
from lspnetd.models.device import NetworkInterfaceState


def dump_interface_state(namespace: str, name: str):
    addr_output = sudo_call_output(ns_wrap(namespace, ["ip", "-j", "addr", "show", "dev", name]))
    addr_output = json.loads(addr_output)[0]

    return NetworkInterfaceState(
        name=name,
        mtu=addr_output['mtu'],
        up='UP' in addr_output['flags'] and 'LOWER_UP' in addr_output['flags'],
        all_ipv4=[f"{addr['local']}/{addr['prefixlen']}" for addr in addr_output['addr_info'] if addr['family'] == 'inet'],
        all_ipv6=[f"{addr['local']}/{addr['prefixlen']}" for addr in addr_output['addr_info'] if addr['family'] == 'inet6'],
    )


def dump_all_interface_state(namespace: str):
    output = sudo_call_output(ns_wrap(namespace, ["ip", "-j", "addr", "show"]))
    output = json.loads(output)
    
    return [NetworkInterfaceState(
        name=addr_output['ifname'],
        mtu=addr_output['mtu'],
        up='UP' in addr_output['flags'] and 'LOWER_UP' in addr_output['flags'],
        all_ipv4=[f"{addr['local']}/{addr['prefixlen']}" for addr in addr_output['addr_info'] if addr['family'] == 'inet'],
        all_ipv6=[f"{addr['local']}/{addr['prefixlen']}" for addr in addr_output['addr_info'] if addr['family'] == 'inet6'],
    ) for addr_output in output]


def up_interface(namespace: str, name: str):
    sudo_call_output(ns_wrap(namespace, ["ip", "link", "set", "dev", name, "up"]))


def destroy_interface(namespace: str, name: str):
    sudo_call_output(ns_wrap(namespace, ["ip", "link", "delete", "dev", name]))


def destroy_interface_if_exists(namespace: str, name: str):
    if [iface for iface in dump_all_interface_state(namespace) if iface.name == name]:
        destroy_interface(namespace, name)
