#!/usr/bin/env python3

from __future__ import annotations

from cli import CliArgs
from tx import Tx

CliArgs.parse_cli_args()
Tx.run()
