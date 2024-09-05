# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright © 2024 Nicolas Graves <ngraves@ngraves.fr>

from typing import Any
from .main import (direnv_values, find_direnv, is_allowed, load_direnv)


def load_ipython_extension(ipython: Any) -> None:
    from .ipython import load_ipython_extension
    load_ipython_extension(ipython)


__all__ = ['load_direnv',
           'direnv_values',
           'find_direnv',
           'is_allowed',
           'load_ipython_extension']
