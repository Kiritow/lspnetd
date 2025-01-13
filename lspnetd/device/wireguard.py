import tempfile
from lspnetd.common.utils import ns_wrap, sudo_call, sudo_call_output, hostport_resolve
from lspnetd.models.device import WireGuardDevicePeerState, WireGuardDeviceState


def dump_wireguard_state(namespace: str, device_name: str):
    output = sudo_call_output(ns_wrap(namespace, ["wg", "show", device_name, "dump"]))
    state: WireGuardDeviceState | None = None

    for line in output.split('\n'):
        if not line:
            continue
        parts = line.split('\t')

        if len(parts) == 4:
            state = WireGuardDeviceState(
                name=device_name,
                private=parts[0],
                public=parts[1],
                listen=int(parts[2]),
                fwmark=0 if parts[3] == 'off' else int(parts[3]),
                peers=[],
            )
        else:
            assert state is not None
            state.peers.append(WireGuardDevicePeerState(
                public=parts[0],
                preshared='' if parts[1] == '(none)' else parts[1],
                endpoint='' if parts[2] == '(none)' else parts[2],
                allowed_ips=parts[3].split(","),
                latest_handshake=int(parts[4]),
                rx=int(parts[5]),
                tx=int(parts[6]),
                keepalive=0 if parts[7] == 'off' else int(parts[7]),
            ))

    return state


def dump_all_wireguard_state(namespace: str) -> list[WireGuardDeviceState]:
    output = sudo_call_output(ns_wrap(namespace, ["wg", "show", "all", "dump"]))
    state_map: dict[str, WireGuardDeviceState] = {}

    for line in output.split('\n'):
        if not line:
            continue
        parts = line.split('\t')
        if parts[0] not in state_map:
            # new interface
            state_map[parts[0]] = WireGuardDeviceState(
                name=parts[0],
                private=parts[1],
                public=parts[2],
                listen=int(parts[3]),
                fwmark=0 if parts[4] == 'off' else int(parts[4]),
                peers=[],    
            )
        else:
            state_map[parts[0]].peers.append(WireGuardDevicePeerState(
                public=parts[1],
                preshared='' if parts[2] == '(none)' else parts[2],
                endpoint='' if parts[3] == '(none)' else parts[3],
                allowed_ips=parts[4].split(","),
                latest_handshake=int(parts[5]),
                rx=int(parts[6]),
                tx=int(parts[7]),
                keepalive=0 if parts[8] == 'off' else int(parts[8]),
            ))

    return list(state_map.values())


def create_wg_device(namespace: str, name: str, address: str, mtu: int):
    sudo_call(["ip", "link", "add", "dev", name, "type", "wireguard"])
    if namespace:
        # move to namespace. this is required for wireguard to work, because wireguard will "remeber" where the device was created
        # DO NOT change to ip link add <> netns <>
        sudo_call(["ip", "link", "set", "dev", name, "netns", namespace])

    sudo_call(ns_wrap(namespace, ["ip", "address", "add", "dev", name, address]))
    sudo_call(ns_wrap(namespace, ["ip", "link", "set", "dev", name, "mtu", str(mtu)]))


def assign_wg_device(namespace: str, name: str, private_key: str, listen_port: int, peer: str, endpoint: str, keepalive: int, allowed_ips: list[str] | str):
    config_args: list[str] = []

    if listen_port:
        config_args.extend(["listen-port", str(listen_port)])
    if peer:
        config_args.extend(["peer", peer])
        if endpoint:
            host, port = hostport_resolve(endpoint)
            config_args.extend(["endpoint", f"{host}:{port or 51820}"])
        if keepalive:
            config_args.extend(["persistent-keepalive", str(keepalive)])
        if allowed_ips:
            config_args.extend(["allowed-ips", ",".join(allowed_ips) if isinstance(allowed_ips, list) else allowed_ips])

    with tempfile.NamedTemporaryFile(mode='w+b', delete=False) as f:
        temp_filename = f.name
        f.write(private_key.encode())
        f.flush()
        config_args = ["private-key", temp_filename] + config_args

        sudo_call(ns_wrap(namespace, ["wg", "set", name] + config_args))
