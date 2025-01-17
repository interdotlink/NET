class IntfStats:
    """
    Class to store stats per interface
    """

    tx_pks_last = 0
    tx_pks = 0


class Stats:
    """
    Class to store all interface stats
    """

    intfs: dict[str, IntfStats] = {}
