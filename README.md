# NETwork Entropy Tester

NETwork Entropy Tester can be used to generate a stream of packets with changing entropy.

When sending traffic out of a single interface, NET will increment in every packet some piece of header entropy as specified by the CLI args. For example, to test how a network device load-balances traffic by hashing on various packet header fields, NET can be used to send traffic out of a single interface, into a router, and the router may then forward that traffic onwards over a LAG or ECMP path.

When sending traffic out of more than one interface, NET still increments the header entropy data in every packet, but it also performs per-packet round-robin transmission of the packets across all interfaces.

```text
            ECMP               LAG                ECMP
┌────────┐ ─────► ┌─────────┐ ─────► ┌─────────┐ ─────► ┌──────┐
│ NET Tx │ ─────► │ Router1 │ ─────► │ Router2 │ ─────► │ Sink │
└────────┘ ─────► └─────────┘ ─────► └─────────┘ ─────► └──────┘
```

## Features

```shell
$ python3 ./net.py -h
usage: net.py [-h] [-d D] [-g G] -i I [-s] [-p] [--l2-dst] [--l2-src] [--l2-inner] [--dst-mac DST_MAC] [--src-mac SRC_MAC] [-m] [--mpls-label] [-6] [--l3-dst]
              [--l3-src] [--dst-ipv4 DST_IPV4] [--src-ipv4 SRC_IPV4] [--dst-ipv6 DST_IPV6] [--src-ipv6 SRC_IPV6] [-u] [--l4-dst] [--l4-src]

Net Entropy Tester - Send packets with changing entropy

options:
  -h, --help           show this help message and exit
  -d D                 Duration to transmit for in seconds. (default: 10)
  -g G                 Inter-packet gap in seconds. Must be >= 0.0 and <= 60.0. Anything higher than 0.0 is reducing the pps rate. (default: 0.0)
  -i I                 Interface(s) to transmit on. This can be specified multiple times to round-robin packets across multiple interfaces. (default: [])
  -s                   Print stats during test (lowers pps rate). (default: False)
  -p                   Print the protocol stack which is being sent. (default: False)

Ethernet Settings:
  --l2-dst             Change the inner most destination MAC address per-frame. (default: False)
  --l2-src             Change the inner most source MAC address per-frame. (default: False)
  --l2-inner           Add an inner Ethernet header after the MPLS label(s) stack. This will automatically insert the Pseudowire Control-World. Requires -m at least
                       once. (default: False)
  --dst-mac DST_MAC    Set the initial destination MAC. (default: 00:00:00:00:00:02)
  --src-mac SRC_MAC    Set the initial source MAC. (default: 00:00:00:00:00:01)

MPLS Settings:
  -m                   Insert an MPLS label after the outer Ethernet header. Specify -m multiple times to stack multiple MPLS labels. (default: None)
  --mpls-label         Change the inner most MPLS label per-frame. (default: False)

L3 Settings:
  -6                   Use IPv6 instead of IPv4. (default: False)
  --l3-dst             Change the destination IP address per-packet. (default: False)
  --l3-src             Change the source IP address per-packet. (default: False)
  --dst-ipv4 DST_IPV4  Set the initial destination IPv4 address. (default: 10.201.201.2)
  --src-ipv4 SRC_IPV4  Set the initial source IPv4 address. (default: 10.201.201.1)
  --dst-ipv6 DST_IPV6  Set the initial destination IPv6 address. (default: FD00::0201:2)
  --src-ipv6 SRC_IPV6  Set the initial source IPv6 address (default: FD00::0201:1)

L4 Settings:
  -u                   Use UDP instead of TCP. (default: False)
  --l4-dst             Change the destination port per-datagram. (default: False)
  --l4-src             Change the source port per-datagram. (default: False)
```

## Install

```shell
python3 -m venv --without-pip .venv && source .venv/bin/activate
python3 -m ensurepip
python3 -m pip install -r requirements.txt
python3 -m pip freeze -l
./net.py -h
```

You need to run net.py as root in order to use raw sockets. When using sudo a different Python interpreter is used than the one in the venv you just set up, which will be missing the dependencies, therefore you use `sudo -E $(which python3) ./net.py` throughout this README. This is not needed if you are NOT using a venv or running in Docker.

## Example

```shell
# Create two veth pairs we can load-balance traffic over
sudo ip netns add NS1 && \
sudo ip netns add NS2 && \
sudo ip link add veth0 type veth peer name veth1 && \
sudo ip link add veth2 type veth peer name veth3 && \
sudo ip link set veth1 netns NS1 && \
sudo ip link set veth3 netns NS2 && \
sudo ip netns exec NS1 ip link set up dev veth1 && \
sudo ip netns exec NS2 ip link set up dev veth3 && \
sudo sysctl -w net.ipv6.conf.veth0.disable_ipv6=1 && \
sudo ip netns exec NS1 sysctl -w net.ipv6.conf.veth1.disable_ipv6=1 && \
sudo sysctl -w net.ipv6.conf.veth2.disable_ipv6=1 && \
sudo ip netns exec NS2 sysctl -w net.ipv6.conf.veth3.disable_ipv6=1 && \
sudo ip link set up dev veth0 && \
sudo ip link set up dev veth2

# Send traffic over both interfaces for 1 second with a rotating source IP address:
$ sudo -E $(which python3) ./net.py -i veth0 -i veth2 --l3-src -d 1
Going to transmit for 1 seconds using interface(s) ['veth0', 'veth2']

Starting at 2024-02-07 17:41:42.335506
Finished at 2024-02-07 17:41:43.414516
Sent 4814 packets

# Using tcpdump on one interface, we see the odd numbered source IPs:
$ sudo tcpdump -i veth0 -c 3 -t 2>/dev/null
IP 10.201.201.1.1024 > 10.201.201.2.1024: Flags [S], seq 0, win 8192, length 0
IP 10.201.201.3.1024 > 10.201.201.2.1024: Flags [S], seq 0, win 8192, length 0
IP 10.201.201.5.1024 > 10.201.201.2.1024: Flags [S], seq 0, win 8192, length 0

# Using tcpdump on the other interface we see the even numbered source IPs:
$ sudo tcpdump -i veth2 -c 3 -t 2>/dev/null
IP 10.201.201.2.1024 > 10.201.201.2.1024: Flags [S], seq 0, win 8192, length 0
IP 10.201.201.4.1024 > 10.201.201.2.1024: Flags [S], seq 0, win 8192, length 0
IP 10.201.201.6.1024 > 10.201.201.2.1024: Flags [S], seq 0, win 8192, length 0
```
