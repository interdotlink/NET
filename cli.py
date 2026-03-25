from __future__ import annotations

import argparse
import ipaddress
from typing import Any

from settings import Settings


class CliArgs:
    """
    Generate and parse CLI args, updating the application settings with the
    results
    """

    @staticmethod
    def create_parser() -> argparse.ArgumentParser:
        """
        Create the CLI parser with all desired CLI options
        """
        parser = argparse.ArgumentParser(
            description="Net Entropy Tester - Send packets with changing entropy",
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        )

        parser.add_argument(
            "-d",
            help="Duration to transmit for in seconds.",
            type=int,
            required=False,
            default=Settings.max_duration,
        )
        parser.add_argument(
            "-g",
            help="Inter-packet gap in seconds. Must be >= 0.0 and <= 60.0. "
            "Anything higher than 0.0 is reducing the pps rate.",
            type=float,
            required=False,
            default=Settings.inter_packet_gap,
        )
        parser.add_argument(
            "-i",
            help="Interface(s) to transmit on. This can be specified multiple "
            "times to round-robin packets across multiple interfaces.",
            type=str,
            required=True,
            action='append',
            default=Settings.interfaces,
        )
        parser.add_argument(
            "-s",
            help="Print stats during test (lowers pps rate).",
            action="store_true",
            required=False,
            default=Settings.running_stats,
        )
        parser.add_argument(
            "-p",
            help="Print the protocol stack which is being sent.",
            action="store_true",
            required=False,
            default=Settings.print_packet,
        )

        eth_args = parser.add_argument_group("Ethernet Settings")
        eth_args.add_argument(
            "--l2-dst",
            help="Change the inner most destination MAC address per-frame.",
            default=Settings.ethernet_dst_rotate,
            action="store_true",
            required=False,
        )
        eth_args.add_argument(
            "--l2-src",
            help="Change the inner most source MAC address per-frame.",
            default=Settings.ethernet_src_rotate,
            action="store_true",
            required=False,
        )
        eth_args.add_argument(
            "--l2-inner",
            help="Add an inner Ethernet header after the MPLS label(s) stack. "
            "This will automatically insert the Pseudowire Control-World. "
            "Requires -m at least once.",
            default=Settings.ethernet_inner,
            action="store_true",
            required=False,
        )
        eth_args.add_argument(
            "--dst-mac",
            help=f"Set the initial destination MAC.",
            default=Settings.ethernet_dst,
            type=str,
            required=False,
        )
        eth_args.add_argument(
            "--src-mac",
            help=f"Set the initial source MAC.",
            default=Settings.ethernet_src,
            type=str,
            required=False,
        )

        mpls_args = parser.add_argument_group("VLAN Settings")
        mpls_args.add_argument(
            "-v",
            help="Insert VLAN ID after the outer Ethernet header "
            "(before any MPLS labels). "
            "Specify -v multiple times to stack multiple VLAN IDs.",
            default=None,
            action="count",
            required=False,
        )
        mpls_args.add_argument(
            "--vlan-id",
            help="Change the inner most VLAN ID per-frame.",
            default=False,
            action="store_true",
            required=False,
        )

        mpls_args = parser.add_argument_group("MPLS Settings")
        mpls_args.add_argument(
            "-m",
            help="Insert an MPLS label after the outer Ethernet header. "
            "Specify -m multiple times to stack multiple MPLS labels.",
            default=None,
            action="count",
            required=False,
        )
        mpls_args.add_argument(
            "--mpls-label",
            help="Change the inner most MPLS label per-frame.",
            default=False,
            action="store_true",
            required=False,
        )

        ip_args = parser.add_argument_group("L3 Settings")
        ip_args.add_argument(
            "-6",
            help="Use IPv6 instead of IPv4.",
            default=Settings.ipv6,
            action="store_true",
            required=False,
        )
        ip_args.add_argument(
            "-t",
            help="TTL",
            default=Settings.ip_ttl,
            type=int,
            required=False,
        )
        ip_args.add_argument(
            "--l3-dst",
            help="Change the destination IP address per-packet.",
            default=Settings.ip_dst_rotate,
            action="store_true",
            required=False,
        )
        ip_args.add_argument(
            "--l3-src",
            help="Change the source IP address per-packet.",
            default=Settings.ip_src_rotate,
            action="store_true",
            required=False,
        )
        ip_args.add_argument(
            "--dst-ipv4",
            help=f"Set the initial destination IPv4 address.",
            default=Settings.ipv4_dst,
            type=str,
            required=False,
        )
        ip_args.add_argument(
            "--src-ipv4",
            help=f"Set the initial source IPv4 address.",
            default=Settings.ipv4_src,
            type=str,
            required=False,
        )
        ip_args.add_argument(
            "--dst-ipv6",
            help=f"Set the initial destination IPv6 address.",
            default=Settings.ipv6_dst,
            type=str,
            required=False,
        )
        ip_args.add_argument(
            "--src-ipv6",
            help=f"Set the initial source IPv6 address",
            default=Settings.ipv6_src,
            type=str,
            required=False,
        )

        l4_args = parser.add_argument_group("L4 Settings")
        l4_protocol_group = l4_args.add_mutually_exclusive_group()
        l4_protocol_group.add_argument(
            "-u",
            help="Use UDP instead of TCP.",
            default=Settings.udp,
            action="store_true",
            required=False,
        )
        l4_protocol_group.add_argument(
            "-I",
            help="Use ICMP instead of TCP.",
            default=Settings.icmp,
            action="store_true",
            required=False,
        )
        l4_args.add_argument(
            "--l4-dst",
            help="Change the destination port per-datagram (TCP & UDP).",
            default=Settings.l4_dst_rotate,
            action="store_true",
            required=False,
        )
        l4_args.add_argument(
            "--l4-src",
            help="Change the source port per-datagram (TCP & UDP).",
            default=Settings.l4_src_rotate,
            action="store_true",
            required=False,
        )
        l4_args.add_argument(
            "--l4-seq",
            help="Change the sequence number per-datagram (ICMP).",
            default=Settings.l4_seq_rotate,
            action="store_true",
            required=False,
        )

        return parser

    @staticmethod
    def parse_cli_args() -> dict[str, Any]:
        """
        Parse the CLI args and update the settings
        """
        parser = CliArgs.create_parser()
        args = vars(parser.parse_args())

        if args["g"] < 0.0 or args["g"] > 60.0:
            raise ValueError(f"-g must be >= 0.0 and <= 60.0, not {args['g']}")

        if args["mpls_label"] and not args["m"]:
            raise ValueError(f"--mpls-label requires -m")

        if args["vlan_id"] and not args["v"]:
            raise ValueError(f"--vlan-id requires -v")

        if args["l2_inner"] and not args["m"]:
            raise ValueError(f"--l2-inner requires -m")

        assert (
            type(ipaddress.ip_address(args["dst_ipv4"]))
            == ipaddress.IPv4Address
        )
        assert (
            type(ipaddress.ip_address(args["src_ipv4"]))
            == ipaddress.IPv4Address
        )
        assert (
            type(ipaddress.ip_address(args["dst_ipv6"]))
            == ipaddress.IPv6Address
        )
        assert (
            type(ipaddress.ip_address(args["src_ipv6"]))
            == ipaddress.IPv6Address
        )

        Settings.max_duration = args["d"]
        Settings.inter_packet_gap = args["g"]
        Settings.interfaces = args["i"]
        Settings.running_stats = args["s"]
        Settings.print_packet = args["p"]
        Settings.ethernet_dst_rotate = args["l2_dst"]
        Settings.ethernet_src_rotate = args["l2_src"]
        Settings.ethernet_dst = args["dst_mac"]
        Settings.ethernet_src = args["src_mac"]
        Settings.ethernet_inner = args["l2_inner"]
        Settings.ethernet_vlan = args["v"]
        Settings.ethernet_vlan_rotate = args["vlan_id"]
        Settings.mpls = args["m"]
        Settings.mpls_rotate = args["mpls_label"]
        Settings.ip_dst_rotate = args["l3_dst"]
        Settings.ip_src_rotate = args["l3_src"]
        Settings.ip_ttl = args["t"]
        Settings.ipv4_dst = args["dst_ipv4"]
        Settings.ipv4_src = args["src_ipv4"]
        Settings.ipv6 = args["6"]
        Settings.ipv6_dst = args["dst_ipv6"]
        Settings.ipv6_src = args["src_ipv6"]
        Settings.l4_dst_rotate = args["l4_dst"]
        Settings.l4_src_rotate = args["l4_src"]
        Settings.udp = args["u"]
        Settings.icmp = args["I"]
        Settings.l4_seq_rotate = args["l4_seq"]

        if (
            Settings.ethernet_dst_rotate
            or Settings.ethernet_src_rotate
            or Settings.ethernet_vlan_rotate
            or Settings.mpls_rotate
            or Settings.ip_dst_rotate
            or Settings.ip_src_rotate
            or Settings.l4_dst_rotate
            or Settings.l4_src_rotate
            or Settings.l4_seq_rotate
        ):
            Settings.rotate = True

        return args
