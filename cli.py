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
            default=Settings.MAX_DURATION,
        )
        parser.add_argument(
            "-g",
            help="Inter-packet gap in seconds. Must be >= 0.0 and <= 60.0. "
            "Anything higher than 0.0 is reducing the pps rate.",
            type=float,
            required=False,
            default=Settings.INTER_PACKET_GAP,
        )
        parser.add_argument(
            "-i",
            help="Interface(s) to transmit on. This can be specified multiple "
            "times to round-robin packets across multiple interfaces.",
            type=str,
            required=True,
            action='append',
            default=Settings.INTERFACES,
        )
        parser.add_argument(
            "-s",
            help="Print stats during test (lowers pps rate).",
            action="store_true",
            required=False,
            default=Settings.RUNNING_STATS,
        )
        parser.add_argument(
            "-p",
            help="Print the protocol stack which is being sent.",
            action="store_true",
            required=False,
            default=Settings.PRINT_PACKET,
        )

        eth_args = parser.add_argument_group("Ethernet Settings")
        eth_args.add_argument(
            "--l2-dst",
            help="Change the inner most destination MAC address per-frame.",
            default=False,
            action="store_true",
            required=False,
        )
        eth_args.add_argument(
            "--l2-src",
            help="Change the inner most source MAC address per-frame.",
            default=False,
            action="store_true",
            required=False,
        )
        eth_args.add_argument(
            "--l2-inner",
            help="Add an inner Ethernet header after the MPLS label(s) stack. "
            "This will automatically insert the Pseudowire Control-World. "
            "Requires -m at least once.",
            default=False,
            action="store_true",
            required=False,
        )
        eth_args.add_argument(
            "--dst-mac",
            help=f"Set the initial destination MAC.",
            default=Settings.ETHERNET_DST,
            type=str,
            required=False,
        )
        eth_args.add_argument(
            "--src-mac",
            help=f"Set the initial source MAC.",
            default=Settings.ETHERNET_SRC,
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
            default=False,
            action="store_true",
            required=False,
        )
        ip_args.add_argument(
            "--l3-dst",
            help="Change the destination IP address per-packet.",
            default=False,
            action="store_true",
            required=False,
        )
        ip_args.add_argument(
            "--l3-src",
            help="Change the source IP address per-packet.",
            default=False,
            action="store_true",
            required=False,
        )
        ip_args.add_argument(
            "--dst-ipv4",
            help=f"Set the initial destination IPv4 address.",
            default=Settings.IPV4_DST,
            type=str,
            required=False,
        )
        ip_args.add_argument(
            "--src-ipv4",
            help=f"Set the initial source IPv4 address.",
            default=Settings.IPV4_SRC,
            type=str,
            required=False,
        )
        ip_args.add_argument(
            "--dst-ipv6",
            help=f"Set the initial destination IPv6 address.",
            default=Settings.IPV6_DST,
            type=str,
            required=False,
        )
        ip_args.add_argument(
            "--src-ipv6",
            help=f"Set the initial source IPv6 address",
            default=Settings.IPV6_SRC,
            type=str,
            required=False,
        )

        tcp_args = parser.add_argument_group("L4 Settings")
        tcp_args.add_argument(
            "-u",
            help="Use UDP instead of TCP.",
            default=False,
            action="store_true",
            required=False,
        )
        tcp_args.add_argument(
            "--l4-dst",
            help="Change the destination port per-datagram.",
            default=False,
            action="store_true",
            required=False,
        )
        tcp_args.add_argument(
            "--l4-src",
            help="Change the source port per-datagram.",
            default=False,
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

        Settings.MAX_DURATION = args["d"]
        Settings.INTER_PACKET_GAP = args["g"]
        Settings.INTERFACES = args["i"]
        Settings.RUNNING_STATS = args["s"]
        Settings.PRINT_PACKET = args["p"]
        Settings.ETHERNET_DST_ROTATE = args["l2_dst"]
        Settings.ETHERNET_SRC_ROTATE = args["l2_src"]
        Settings.ETHERNET_DST = args["dst_mac"]
        Settings.ETHERNET_SRC = args["src_mac"]
        Settings.ETHERNET_INNER = args["l2_inner"]
        Settings.ETHERNET_VLAN = args["v"]
        Settings.ETHERNET_VLAN_ROTATE = args["vlan_id"]
        Settings.MPLS = args["m"]
        Settings.MPLS_ROTATE = args["mpls_label"]
        Settings.IP_DST_ROTATE = args["l3_dst"]
        Settings.IP_SRC_ROTATE = args["l3_src"]
        Settings.IPV4_DST = args["dst_ipv4"]
        Settings.IPV4_SRC = args["src_ipv4"]
        Settings.IPV6 = args["6"]
        Settings.IPV6_DST = args["dst_ipv6"]
        Settings.IPV6_SRC = args["src_ipv6"]
        Settings.L4_DST_ROTATE = args["l4_dst"]
        Settings.L4_SRC_ROTATE = args["l4_src"]
        Settings.UDP = args["u"]

        if (
            Settings.ETHERNET_DST_ROTATE
            or Settings.ETHERNET_SRC_ROTATE
            or Settings.ETHERNET_VLAN_ROTATE
            or Settings.MPLS_ROTATE
            or Settings.IP_DST_ROTATE
            or Settings.IP_SRC_ROTATE
            or Settings.L4_DST_ROTATE
            or Settings.L4_SRC_ROTATE
        ):
            Settings.ROTATE = True

        return args
