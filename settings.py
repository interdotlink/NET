from typing import Optional

from scapy.packet import Packet  # type: ignore

from stats import Stats


class Settings:
    # L2 Settings
    ETHERNET_DST = "00:00:00:00:00:02"
    ETHERNET_DST_ROTATE = False
    ETHERNET_INNER = False
    ETHERNET_MAX_ADDR = 281474976710655
    ETHERNET_MIN_ADDR = 0
    ETHERNET_SRC = "00:00:00:00:00:01"
    ETHERNET_SRC_ROTATE = False
    ETHERNET_VLAN: Optional[int] = None
    ETHERNET_VLAN_MAX = 4094
    ETHERNET_VLAN_MIN = 0
    ETHERNET_VLAN_ROTATE = False

    # L2.5 Settings
    MPLS: Optional[int] = None
    MPLS_MAX = 1048575
    MPLS_MIN = 0
    MPLS_ROTATE = False
    MPLS_UNALLOCATED = 256

    # L3 Settings
    IP_DST_ROTATE = False
    IP_SRC_ROTATE = False
    IPV4_DST = "10.201.201.2"
    IPV4_MAX = 4294967295
    IPV4_MIN = 0
    IPV4_SRC = "10.201.201.1"
    IPV6 = False
    IPV6_DST = "FD00::0201:2"
    IPV6_MAX = 340282366920938463463374607431768211455
    IPV6_MIN = 0
    IPV6_SRC = "FD00::0201:1"

    # L4 Settings
    L4_DST_ROTATE = False
    L4_SRC_ROTATE = False
    L4_MAX = 65535
    L4_MIN = 1024
    UDP = False

    # Test Settings
    DURATION = 0
    MAX_DURATION = 10
    INTER_PACKET_GAP = 0.0
    INTERFACES: list[str] = []
    LAYER_ETH = 0
    LAYER_ETH_INNER = 0
    LAYER_ETH_ROTATE = 0
    LAYER_VLAN_FIRST = 0
    LAYER_VLAN_LAST = 0
    LAYER_MPLS_FIRST = 0
    LAYER_MPLS_LAST = 0
    LAYER_IP = 0
    LAYER_4 = 0
    PACKET: Optional[Packet] = None
    PRINT_PACKET = False
    ROTATE = False
    RUNNING_STATS = False
    STATS = Stats()
    STATS_INTERVAL = 1
    TRANSMITTING = False
