from __future__ import annotations

from ipaddress import IPv4Address, IPv6Address, ip_address
from textwrap import wrap

from scapy.contrib.mpls import MPLS, EoMCW  # type: ignore
from scapy.layers.inet import ICMP, IP, TCP, UDP, Ether  # type: ignore
from scapy.layers.inet6 import ICMPv6EchoRequest, IPv6  # type: ignore
from scapy.layers.l2 import Dot1Q  # type: ignore
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

    outer_dst_mac = Settings.ethernet_dst
    inner_dst_mac = Settings.ethernet_dst
    """
    If --l2-src option is used, set the starting source mac to be the destination MAC + 1.
    If the source is 00:00:00:00:00:01 and destination is "00:00:00:00:00:02, the 2nd packet
    will have the same source and destination MAC, causing a MAC move (if testing EVPN).
    """
    if Settings.ethernet_src_rotate:
        if Settings.ethernet_inner:
            inner_src_mac = rotate_mac(Settings.ethernet_dst)
            outer_src_mac = Settings.ethernet_src
        else:
            inner_src_mac = Settings.ethernet_src
            outer_src_mac = rotate_mac(Settings.ethernet_dst)
    else:
        outer_src_mac = Settings.ethernet_src
        inner_src_mac = Settings.ethernet_src

    vlan = Settings.ethernet_vlan_min

    label = Settings.mpls_min

    if Settings.ipv6:
        dst_ip = Settings.ipv6_dst
        src_ip = Settings.ipv6_src
    else:
        dst_ip = Settings.ipv4_dst
        src_ip = Settings.ipv4_src
    ttl = Settings.ip_ttl

    dst_port = Settings.l4_min
    src_port = Settings.l4_min
    icmp_seq = Settings.l4_seq_min

    """
    Next, build the header stack using the defaults.
    Record the index/layer of each header in the Scapy packet.
    """

    packet = Ether(dst=outer_dst_mac, src=outer_src_mac)
    Settings.layer_eth = 0

    if Settings.ethernet_vlan:
        for _ in range(0, Settings.ethernet_vlan):
            packet.add_payload(Dot1Q(vlan=vlan))
        Settings.layer_vlan_first = Settings.layer_eth + 1  # Outer most VLAN
        Settings.layer_vlan_last = (
            Settings.layer_eth + Settings.ethernet_vlan
        )  # Inner most VLAN
    else:
        Settings.layer_vlan_first = Settings.layer_eth
        Settings.layer_vlan_last = Settings.layer_vlan_first

    if Settings.mpls:
        for _ in range(0, Settings.mpls):
            packet.add_payload(MPLS(label=label))
        Settings.layer_mpls_first = Settings.layer_eth + 1  # Outer most label
        Settings.layer_mpls_last = (
            Settings.layer_eth + Settings.mpls
        )  # Inner most label
    else:
        Settings.layer_mpls_first = Settings.layer_eth
        Settings.layer_mpls_last = Settings.layer_mpls_first

    if Settings.ethernet_inner:
        # non-IP payload, start from a label which is not IP related
        packet[Settings.layer_mpls_last].label = Settings.mpls_unallocated
        packet.add_payload(EoMCW())
        packet.add_payload(Ether(dst=inner_dst_mac, src=inner_src_mac))
        Settings.layer_eth_inner = Settings.layer_mpls_last + 2
        Settings.layer_eth_rotate = Settings.layer_eth_inner
    else:
        Settings.layer_eth_inner = Settings.layer_mpls_last
        Settings.layer_eth_rotate = Settings.layer_eth

    if Settings.ipv6:
        packet.add_payload(IPv6(dst=dst_ip, src=src_ip, hlim=ttl))
    else:
        packet.add_payload(IP(dst=dst_ip, src=src_ip, ttl=ttl))
    Settings.layer_ip = Settings.layer_eth_inner + 1

    if Settings.udp:
        packet.add_payload(UDP(dport=dst_port, sport=src_port))
    elif Settings.icmp:
        if Settings.ipv6:
            packet.add_payload(ICMPv6EchoRequest(seq=icmp_seq))
        else:
            packet.add_payload(ICMP(seq=icmp_seq))
    else:
        packet.add_payload(TCP(dport=dst_port, sport=src_port))
    Settings.layer_4 = Settings.layer_ip + 1

    Settings.packet = packet

    if Settings.print_packet:
        print("Base packet is:")
        Settings.packet.show2()


def rotate_seq(seq: int) -> int:
    """
    Increment an ICMP sequence number
    """
    if seq < Settings.l4_seq_max:
        seq += 1
    else:
        seq = Settings.l4_seq_min
    return seq


def rotate_port(port: int) -> int:
    """
    Increment a L4 port number
    """
    if port < Settings.l4_max:
        port += 1
    else:
        port = Settings.l4_min
    return port


def rotate_ipv4(ip_addr: str) -> str:
    """
    Increment an IPv4 address
    """
    addr = int(IPv4Address(ip_addr))
    if addr < Settings.ipv4_max:
        addr += 1
    else:
        addr = Settings.ipv4_min
    return str(ip_address(addr))


def rotate_ipv6(ip_addr: str) -> str:
    """
    Increment an IPv6 address
    """
    addr = int(IPv6Address(ip_addr))
    if addr < Settings.ipv6_max:
        addr += 1
    else:
        addr = Settings.ipv6_min
    return str(ip_address(addr)).upper()


def rotate_vlan(vlan: int) -> int:
    """
    Increment a VLAN ID
    """
    if vlan < Settings.ethernet_vlan_max:
        vlan += 1
    else:
        vlan = Settings.ethernet_vlan_min
    return vlan


def rotate_label(label: int) -> int:
    """
    Increment an MPLS label
    """
    if label < Settings.mpls_max:
        label += 1
    else:
        label = Settings.mpls_min
    return label


def rotate_mac(mac_addr: str) -> str:
    """
    Increment a MAC address
    """
    addr = int("".join(mac_addr.split(":")), 16)
    if addr < Settings.ethernet_max_addr:
        addr += 1
    else:
        addr = Settings.ethernet_min_addr
    return ":".join(wrap(text=f"{addr:012X}", width=2))


def rotate_values() -> None:
    """
    Rotate the values in the protocol headers until they reach they max,
    then wrap around and start again.
    """

    assert isinstance(Settings.packet, Packet)  # mypy

    if Settings.ethernet_dst_rotate:
        Settings.packet[Settings.layer_eth_rotate].dst = rotate_mac(
            Settings.packet[Settings.layer_eth_rotate].dst
        )

    if Settings.ethernet_src_rotate:
        Settings.packet[Settings.layer_eth_rotate].src = rotate_mac(
            Settings.packet[Settings.layer_eth_rotate].src
        )

    if Settings.ethernet_vlan_rotate:
        Settings.packet[Settings.layer_vlan_last].vlan = rotate_vlan(
            Settings.packet[Settings.layer_vlan_last].vlan
        )

    if Settings.mpls_rotate:
        Settings.packet[Settings.layer_mpls_last].label = rotate_label(
            Settings.packet[Settings.layer_mpls_last].label
        )

    if Settings.ip_dst_rotate:
        if Settings.ipv6:
            Settings.packet[Settings.layer_ip].dst = rotate_ipv6(
                Settings.packet[Settings.layer_ip].dst
            )
        else:
            Settings.packet[Settings.layer_ip].dst = rotate_ipv4(
                Settings.packet[Settings.layer_ip].dst
            )

    if Settings.ip_src_rotate:
        if Settings.ipv6:
            Settings.packet[Settings.layer_ip].src = rotate_ipv6(
                Settings.packet[Settings.layer_ip].src
            )
        else:
            Settings.packet[Settings.layer_ip].src = rotate_ipv4(
                Settings.packet[Settings.layer_ip].src
            )

    if Settings.l4_dst_rotate:
        Settings.packet[Settings.layer_4].dport = rotate_port(
            Settings.packet[Settings.layer_4].dport
        )

    if Settings.l4_src_rotate:
        Settings.packet[Settings.layer_4].sport = rotate_port(
            Settings.packet[Settings.layer_4].sport
        )

    if Settings.l4_seq_rotate:
        if Settings.ipv6:
            Settings.packet[Settings.layer_4].seq = rotate_seq(
                Settings.packet[Settings.layer_4].seq
            )
        else:
            Settings.packet[Settings.layer_4].seq = rotate_seq(
                Settings.packet[Settings.layer_4].seq
            )
