from __future__ import annotations

import signal
from datetime import datetime
from threading import Thread
from time import sleep

from scapy.config import conf  # type: ignore

from packet import build_packet, rotate_values
from settings import Settings
from stats import IntfStats


class Tx:
    @staticmethod
    def end(sig, frame) -> None:
        """
        End the test
        """
        Settings.TRANSMITTING = False
        Settings.DURATION = Settings.MAX_DURATION

    @staticmethod
    def run() -> None:
        """
        Setup up and run the test threads
        """
        build_packet()

        print(
            f"Going to transmit for {Settings.MAX_DURATION} seconds using interface(s) "
            f"{Settings.INTERFACES}\n"
        )

        if Settings.RUNNING_STATS:
            # The live stats thread eats up precious CPU cycles, hence optional
            stats_thd = Thread(target=Tx.stats)
            stats_thd.start()

        signal.signal(signal.SIGINT, Tx.end)

        tx_thd = Thread(target=Tx.tx)
        tx_thd.start()

        ctrl_thd = Thread(target=Tx.control)
        sleep(0.5)  # Ensure other threads are ready
        print(f"Starting at {datetime.now()}")
        ctrl_thd.start()

        ctrl_thd.join()
        tx_thd.join()
        if Settings.RUNNING_STATS:
            stats_thd.join()
        print(f"Finished at {datetime.now()}")

        # Print total across all interfaces
        total_tx_pks = 0
        for intf in Settings.INTERFACES:
            total_tx_pks += Settings.STATS.intfs[intf].tx_pks
        print(f"Sent {total_tx_pks} packets")

    @staticmethod
    def control() -> None:
        """
        Start the test and loop until the $stop condition is true
        """

        Settings.TRANSMITTING = True
        while Settings.DURATION < Settings.MAX_DURATION:
            sleep(Settings.STATS_INTERVAL)
            Settings.DURATION += Settings.STATS_INTERVAL

        Settings.TRANSMITTING = False

    @staticmethod
    def stats() -> None:
        """
        Periodically prints the test statistics
        """

        # Wait for start signal
        while not Settings.TRANSMITTING:
            ...

        print("")
        print("| Time | Interface | Tx Pkts | Total Pkts |")
        print("|------|-----------|---------|------------|")
        while Settings.TRANSMITTING:
            """
            The following prints the stats more reliably on the STATS_INTERVAL
            but, it eats way more CPU cycles than sleep() and drops the
            pps rate:

            next_update = Settings.DURATION + 1
            while Settings.DURATION < next_update:
               ...

            Therefor, use sleep to keep the pps rate higher:
            """
            sleep(Settings.STATS_INTERVAL)

            total_diff = 0
            total_tx_pks = 0
            for intf in Settings.INTERFACES:
                intf_stats = Settings.STATS.intfs[intf]
                diff = intf_stats.tx_pks - intf_stats.tx_pks_last
                intf_stats.tx_pks_last = intf_stats.tx_pks
                total_diff += diff
                total_tx_pks += intf_stats.tx_pks
                print(
                    f"| {Settings.DURATION:^4} | {intf:^9} | {diff:^7} | {intf_stats.tx_pks:^10} |"
                )
            print(
                f"| {Settings.DURATION:^4} |     *     | {total_diff:^7} | {total_tx_pks:^10} |"
            )
            print(f"|------|-----------|---------|------------|")
        print("")

    @staticmethod
    def tx() -> None:
        """
        Start a loop which transmits packets
        """

        """
        When calling send()/sendp()/sendpfast() scapy is opening a socket,
        sending the frame, then closing the socket a again. It is SUPER slow.
        Create a socket which stays open for each interface:
        """
        sockets = {}
        for intf in Settings.INTERFACES:
            sockets[intf] = conf.L2socket(iface=intf)

            # Create a stats objects per-intf which will be updated during the test
            Settings.STATS.intfs[intf] = IntfStats()

        # Wait for start signal
        while not Settings.TRANSMITTING:
            ...

        while Settings.TRANSMITTING:
            for intf in Settings.INTERFACES:
                # send(x=Settings.PACKET, iface=intf, verbose=0)  # 30pps !!!
                # sendp(x=Settings.PACKET, iface=intf, verbose=0)  # 24 pps !!!
                # sendpfast(x=Settings.PACKET, iface=intf, pps=10000)  # 15 pps !!!
                sockets[intf].send(x=Settings.PACKET)  # 6k pps :D
                Settings.STATS.intfs[intf].tx_pks += 1
                if Settings.ROTATE:
                    rotate_values()
            """
            This defaults to 0.0.
            This hack is needed to ensure this thread yields to the other
            thread, otherwise this thread hogs the GIL and the other threads
            don't run properly (e.g. the control thread can't count the duration
            properly and the test runs for much longer that it should).
            """
            sleep(Settings.INTER_PACKET_GAP)

        for intf in Settings.INTERFACES:
            sockets[intf].close()
