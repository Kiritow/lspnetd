from dataclasses import dataclass


@dataclass
class WireGuardDevicePeerState:
    public: str
    preshared: str
    endpoint: str
    allowed_ips: list[str]
    latest_handshake: int
    rx: int
    tx: int
    keepalive: int


@dataclass
class WireGuardDeviceState:
    name: str
    private: str
    public: str
    listen: int
    fwmark: int
    peers: list[WireGuardDevicePeerState]


@dataclass
class NetworkInterfaceState:
    name: str
    mtu: int
    up: bool
    all_ipv4: list[str]
    all_ipv6: list[str]

    @property
    def ipv4(self) -> str:
        return self.all_ipv4[0] if self.all_ipv4 else ""
    
    @property
    def ipv6(self) -> str:
        return self.all_ipv6[0] if self.all_ipv6 else ""
