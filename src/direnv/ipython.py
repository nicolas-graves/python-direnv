# SPDX-License-Identifier:  BSD-3-Clause
# Copyright © 2014 Saurabh Kumar (python-dotenv)
# Copyright © 2013, Ted Tieken (django-dotenv-rw),
# Copyright © 2013, Jacob Kaplan-Moss (django-dotenv)

from IPython.core.magic import Magics, line_magic, magics_class  # type: ignore
from IPython.core.magic_arguments import (argument, magic_arguments,  # type: ignore
                                          parse_argstring)  # type: ignore

from .main import find_direnv, load_direnv


@magics_class
class IPythonDirEnv(Magics):

    @magic_arguments()
    @argument(
        '-o', '--override', action='store_true',
        help="Indicate to override existing variables"
    )
    @argument(
        '-v', '--verbose', action='store_true',
        help="Indicate function calls to be verbose"
    )
    @argument('dotenv_path', nargs='?', type=str, default='.envrc',
              help='Search in increasingly higher folders for the `dotenv_path`')
    @line_magic
    def direnv(self, line):
        args = parse_argstring(self.direnv, line)
        # Locate the .envrc file
        dotenv_path = args.dotenv_path
        try:
            dotenv_path = find_direnv(dotenv_path, True, True)
        except IOError:
            print("cannot find .envrc file")
            return

        # Load the .envrc file
        load_direnv(dotenv_path, verbose=args.verbose, override=args.override)


def load_ipython_extension(ipython):
    """Register the %direnv magic."""
    ipython.register_magics(IPythonDirEnv)
