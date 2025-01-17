from __future__ import annotations

from ipaddress import IPv4Address, IPv6Address, ip_address
from textwrap import wrap

from scapy.contrib.mpls import MPLS, EoMCW  # type: ignore
from scapy.layers.inet import IP, TCP, UDP, Ether  # type: ignore
from scapy.layers.inet6 import IPv6  # type: ignore
from scapy.packet import Packet  # type: ignore

from settings import Settings


def build_packet() -> None:
    """
    Build the base packet
    """

    """
    First, build up the default values for each header in the stack,
    based on the CLI args.
    """

    outer_dst_mac = Settings.ETHERNET_DST
    inner_dst_mac = Settings.ETHERNET_DST
    """
    If --l2-src option is used, set the starting source mac to be the destination MAC + 1.
    If the source is 00:00:00:00:00:01 and destination is "00:00:00:00:00:02, the 2nd packet
    will have the same source and destination MAC, causing a MAC move (if testing EVPN).
    """
    if Settings.ETHERNET_SRC_ROTATE:
        if Settings.ETHERNET_INNER:
            inner_src_mac = rotate_mac(Settings.ETHERNET_DST)
            outer_src_mac = Settings.ETHERNET_SRC
        else:
            inner_src_mac = Settings.ETHERNET_SRC
            outer_src_mac = rotate_mac(Settings.ETHERNET_DST)
    else:
        outer_src_mac = Settings.ETHERNET_SRC
        inner_src_mac = Settings.ETHERNET_SRC

    label = Settings.MPLS_MIN

    if Settings.IPV6:
        dst_ip = Settings.IPV6_DST
        src_ip = Settings.IPV6_SRC
    else:
        dst_ip = Settings.IPV4_DST
        src_ip = Settings.IPV4_SRC

    dst_port = Settings.L4_MIN
    src_port = Settings.L4_MIN

    """
    Next, build the header stack using the defaults.
    Record the index/layer of each header in the Scapy packet.
    """

    packet = Ether(dst=outer_dst_mac, src=outer_src_mac)
    Settings.LAYER_ETH = 0

    if Settings.MPLS:
        for _ in range(0, Settings.MPLS):
            packet.add_payload(MPLS(label=label))
        Settings.LAYER_MPLS_FIRST = Settings.LAYER_ETH + 1  # Outer most label
        Settings.LAYER_MPLS_LAST = (
            Settings.LAYER_ETH + Settings.MPLS
        )  # Inner most label
    else:
        Settings.LAYER_MPLS_FIRST = Settings.LAYER_ETH
        Settings.LAYER_MPLS_LAST = Settings.LAYER_MPLS_FIRST

    if Settings.ETHERNET_INNER:
        # non-IP payload, start from a label which is not IP related
        packet[Settings.LAYER_MPLS_LAST].label = Settings.MPLS_UNALLOCATED
        packet.add_payload(EoMCW())
        packet.add_payload(Ether(dst=inner_dst_mac, src=inner_src_mac))
        Settings.LAYER_ETH_INNER = Settings.LAYER_MPLS_LAST + 2
        Settings.LAYER_ETH_ROTATE = Settings.LAYER_ETH_INNER
    else:
        Settings.LAYER_ETH_INNER = Settings.LAYER_MPLS_LAST
        Settings.LAYER_ETH_ROTATE = Settings.LAYER_ETH

    if Settings.IPV6:
        packet.add_payload(IPv6(dst=dst_ip, src=src_ip))
    else:
        packet.add_payload(IP(dst=dst_ip, src=src_ip))
    Settings.LAYER_IP = Settings.LAYER_ETH_INNER + 1

    if Settings.UDP:
        packet.add_payload(UDP(dport=dst_port, sport=src_port))
    else:
        packet.add_payload(TCP(dport=dst_port, sport=src_port))
    Settings.LAYER_4 = Settings.LAYER_IP + 1

    Settings.PACKET = packet

    if Settings.PRINT_PACKET:
        print("Base packet is:")
        Settings.PACKET.show2()


def rotate_ipv4(ip_addr: str) -> str:
    """
    Increment an IPv4 address
    """
    addr = int(IPv4Address(ip_addr))
    if addr < Settings.IPV4_MAX:
        addr += 1
    else:
        addr = Settings.IPV4_MIN
    return str(ip_address(addr))


def rotate_ipv6(ip_addr: str) -> str:
    """
    Increment an IPv6 address
    """
    addr = int(IPv6Address(ip_addr))
    if addr < Settings.IPV6_MAX:
        addr += 1
    else:
        addr = Settings.IPV6_MIN
    return str(ip_address(addr)).upper()


def rotate_label(label: int) -> int:
    """
    Increment an MPLS label
    """
    if label < Settings.MPLS_MAX:
        label += 1
    else:
        label = Settings.MPLS_MIN
    return label


def rotate_mac(mac_addr: str) -> str:
    """
    Increment a MAC address
    """
    addr = int("".join(mac_addr.split(":")), 16)
    if addr < Settings.ETHERNET_MAX_ADDR:
        addr += 1
    else:
        addr = Settings.ETHERNET_MIN_ADDR
    return ":".join(wrap(text=f"{addr:012X}", width=2))


def rotate_port(port: int) -> int:
    """
    Increment a L4 port number
    """
    if port < Settings.L4_MAX:
        port += 1
    else:
        port = Settings.L4_MIN
    return port


def rotate_values() -> None:
    """
    Rotate the values in the protocol headers until they reach they max,
    then wrap around and start again.
    """

    assert isinstance(Settings.PACKET, Packet)  # mypy

    if Settings.ETHERNET_DST_ROTATE:
        Settings.PACKET[Settings.LAYER_ETH_ROTATE].dst = rotate_mac(
            Settings.PACKET[Settings.LAYER_ETH_ROTATE].dst
        )

    if Settings.ETHERNET_SRC_ROTATE:
        Settings.PACKET[Settings.LAYER_ETH_ROTATE].src = rotate_mac(
            Settings.PACKET[Settings.LAYER_ETH_ROTATE].src
        )

    if Settings.MPLS_ROTATE:
        Settings.PACKET[Settings.LAYER_MPLS_LAST].label = rotate_label(
            Settings.PACKET[Settings.LAYER_MPLS_LAST].label
        )

    if Settings.IP_DST_ROTATE:
        if Settings.IPV6:
            Settings.PACKET[Settings.LAYER_IP].dst = rotate_ipv6(
                Settings.PACKET[Settings.LAYER_IP].dst
            )
        else:
            Settings.PACKET[Settings.LAYER_IP].dst = rotate_ipv4(
                Settings.PACKET[Settings.LAYER_IP].dst
            )

    if Settings.IP_SRC_ROTATE:
        if Settings.IPV6:
            Settings.PACKET[Settings.LAYER_IP].src = rotate_ipv6(
                Settings.PACKET[Settings.LAYER_IP].src
            )
        else:
            Settings.PACKET[Settings.LAYER_IP].src = rotate_ipv4(
                Settings.PACKET[Settings.LAYER_IP].src
            )

    if Settings.L4_DST_ROTATE:
        Settings.PACKET[Settings.LAYER_4].dport = rotate_port(
            Settings.PACKET[Settings.LAYER_4].dport
        )

    if Settings.L4_SRC_ROTATE:
        Settings.PACKET[Settings.LAYER_4].sport = rotate_port(
            Settings.PACKET[Settings.LAYER_4].sport
        )
