from typing import Optional

from scapy.packet import Packet  # type: ignore

from stats import Stats


class Settings:
    # L2 Settings
    ethernet_dst = "00:00:00:00:00:02"
    ethernet_dst_rotate = False
    ethernet_inner = False
    ethernet_max_addr = 281474976710655
    ethernet_min_addr = 0
    ethernet_src = "00:00:00:00:00:01"
    ethernet_src_rotate = False
    ethernet_vlan: Optional[int] = None
    ethernet_vlan_max = 4094
    ethernet_vlan_min = 0
    ethernet_vlan_rotate = False

    # L2.5 Settings
    mpls: Optional[int] = None
    mpls_max = 1048575
    mpls_min = 0
    mpls_rotate = False
    mpls_unallocated = 256

    # L3 Settings
    ip_dst_rotate = False
    ip_src_rotate = False
    ip_ttl = 64
    ipv4_dst = "10.201.201.2"
    ipv4_max = 4294967295
    ipv4_min = 0
    ipv4_src = "10.201.201.1"
    ipv6 = False
    ipv6_dst = "FD00::0201:2"
    ipv6_max = 340282366920938463463374607431768211455
    ipv6_min = 0
    ipv6_src = "FD00::0201:1"

    # L4 Settings
    l4_dst_rotate = False
    l4_src_rotate = False
    l4_max = 65535
    l4_min = 1024
    udp = False
    icmp = False
    l4_seq_rotate = False
    l4_seq_min = 0
    l4_seq_max = 65535

    # Test Settings
    duration = 0
    max_duration = 10
    inter_packet_gap = 0.0
    interfaces: list[str] = []
    layer_eth = 0
    layer_eth_inner = 0
    layer_eth_rotate = 0
    layer_vlan_first = 0
    layer_vlan_last = 0
    layer_mpls_first = 0
    layer_mpls_last = 0
    layer_ip = 0
    layer_4 = 0
    packet: Optional[Packet] = None
    print_packet = False
    rotate = False
    running_stats = False
    stats = Stats()
    stats_interval = 1
    transmitting = False
