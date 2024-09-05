# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright © 2024 Nicolas Graves <ngraves@ngraves.fr>

import hashlib
import io
import logging
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import IO, Dict, Iterable, Iterator, Mapping, Optional, Tuple, Union

logger = logging.getLogger(__name__)

# A type alias for a string path to be used for the paths in this file.
# These paths may flow to `open()` and `shutil.move()`; `shutil.move()`
# only accepts string paths, not byte paths or file descriptors. See
# https://github.com/python/typeshed/pull/6832.
StrPath = Union[str, "os.PathLike[str]"]

env_var_pattern = re.compile(r'declare -x (\w+)="(.*)"')


def direnv_file_hash(path):
    """
    Returns the direnv hash of a file.
    """
    abs_path = os.path.abspath(path)
    with open(abs_path, "r", encoding="utf-8") as f:
        content = f.read()
    input_data = f"{abs_path}\n{content}"
    hasher = hashlib.sha256()
    hasher.update(input_data.encode("utf-8"))
    return hasher.hexdigest()


def _xdg_data_home():
    if value := os.environ.get("XDG_DATA_HOME"):
        return value
    else:
        return str(Path.home() / ".local/share")


def is_allowed(path):
    """
    Checks that direnv allows the execution of file.
    """
    file_hash_value = direnv_file_hash(path)
    allowed_file_path = os.path.join(
        _xdg_data_home(), "direnv", "allow", file_hash_value
    )
    if os.path.exists(allowed_file_path):
        with open(allowed_file_path, "r", encoding="utf-8") as f:
            real_path = f.read().strip()
            return os.path.realpath(path) == real_path
    return False


def parse_bash_env(
    stream: io.StringIO, encoding: Optional[str] = "utf-8"
) -> Iterator[Tuple[str, Optional[str]]]:
    """
    Parses the stream and yields key-value pairs.
    """
    for line_num, line in enumerate(stream, 1):
        line = line.strip()
        match = env_var_pattern.match(line)
        if match:
            key = match.group(1)
            value = match.group(2)
            yield key, value
        else:
            logger.warning(f"Could not parse statement on line {line_num}: '{line}'")


def direnv_as_stream(path):
    """
    Sources the .envrc file, output environment as a stream.
    """
    file_path = os.path.abspath(path)
    wd = os.path.dirname(file_path)
    result = subprocess.run(
        f"cd {wd} 2>&1 && source {file_path} 2>&1 && declare -x",
        shell=True,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Failed to source {path}: {result.stderr}")
    return io.StringIO(result.stdout)


# This function is copied from https://github.com/theskumar/python-dotenv
# SPDX-License-Identifier:  BSD-3-Clause
# Copyright © 2014 Saurabh Kumar (python-dotenv)
# Copyright © 2013, Ted Tieken (django-dotenv-rw),
# Copyright © 2013, Jacob Kaplan-Moss (django-dotenv)
def _walk_to_root(path: str) -> Iterator[str]:
    """
    Yield directories starting from the given directory up to the root
    """
    if not os.path.exists(path):
        raise IOError('Starting path not found')

    if os.path.isfile(path):
        path = os.path.dirname(path)

    last_dir = None
    current_dir = os.path.abspath(path)
    while last_dir != current_dir:
        yield current_dir
        parent_dir = os.path.abspath(os.path.join(current_dir, os.path.pardir))
        last_dir, current_dir = current_dir, parent_dir


# This function is copied from https://github.com/theskumar/python-dotenv
# SPDX-License-Identifier:  BSD-3-Clause
# Copyright © 2014 Saurabh Kumar (python-dotenv)
# Copyright © 2013, Ted Tieken (django-dotenv-rw),
# Copyright © 2013, Jacob Kaplan-Moss (django-dotenv)
def find_direnv(
    filename: str = ".envrc",
    raise_error_if_not_found: bool = False,
    usecwd: bool = False,
) -> str:
    """
    Search in increasingly higher folders for the given file

    Returns path to the file if found, or an empty string otherwise
    """

    def _is_interactive():
        """ Decide whether this is running in a REPL or IPython notebook """
        try:
            main = __import__('__main__', None, None, fromlist=['__file__'])
        except ModuleNotFoundError:
            return False
        return not hasattr(main, '__file__')

    if usecwd or _is_interactive() or getattr(sys, 'frozen', False):
        # Should work without __file__, e.g. in REPL or IPython notebook.
        path = os.getcwd()
    else:
        # will work for .py files
        frame = sys._getframe()
        current_file = __file__

        while frame.f_code.co_filename == current_file or not os.path.exists(
            frame.f_code.co_filename
        ):
            assert frame.f_back is not None
            frame = frame.f_back
        frame_filename = frame.f_code.co_filename
        path = os.path.dirname(os.path.abspath(frame_filename))

    for dirname in _walk_to_root(path):
        check_path = os.path.join(dirname, filename)
        if os.path.isfile(check_path):
            return check_path

    if raise_error_if_not_found:
        raise IOError('File not found')

    return ''


def load_direnv(
    dotenv_path: Optional[StrPath] = None,
    stream: Optional[IO[str]] = None,
    verbose: bool = False,
    override: bool = False,
    interpolate: bool = True,
    encoding: Optional[str] = None,
) -> bool:
    """Parse a .envrc file and then load all the variables found as environment variables.

    Parameters:
        dotenv_path: Absolute or relative path to .envrc file.
        stream: Text stream (such as `io.StringIO`) with .envrc content, used if
            `dotenv_path` is `None`.
        verbose: Whether to output a warning the .envrc file is missing.
        override: Whether to override the system environment variables with the variables
            from the `.envrc` file.
        encoding: Ignored.
        interpolate: Ignored.
    Returns:
        Bool: True if at least one environment variable is set else False

    If both `dotenv_path` and `stream` are `None`, `find_direnv()` is used to find the
    .envrc file with it's default parameters. If you need to change the default parameters
    of `find_direnv()`, you can explicitly call `find_direnv()` and pass the result
    to this function as `dotenv_path`.
    """
    if encoding is not None:
        raise NotImplementedError("Use LC_ALL to change the encoding for now.")
    if not interpolate:
        raise NotImplementedError
    env_dict = direnv_values(
        dotenv_path=dotenv_path,
        stream=stream,
        verbose=verbose,
        interpolate=interpolate,
        encoding=encoding,
    )
    for k, v in env_dict.items():
        if k in os.environ and not override:
            continue
        if v is not None:
            os.environ[k] = v

    return True


def direnv_values(
    dotenv_path: Optional[StrPath] = None,
    stream: Optional[IO[str]] = None,
    verbose: bool = False,
    interpolate: bool = True,
    encoding: Optional[str] = None,
) -> Dict[str, Optional[str]]:
    """
    Parse a .envrc file and return its content as a dict.

    The returned dict will have `None` values for keys without values in the .envrc file.
    For example, `foo=bar` results in `{"foo": "bar"}` whereas `foo` alone results in
    `{"foo": None}`

    Parameters:
        dotenv_path: Absolute or relative path to the .envrc file.
        stream: `StringIO` object with .envrc content, used if `dotenv_path` is `None`.
        verbose: Whether to output a warning if the .envrc file is missing.
        interpolate: Ignored.
        encoding: Ignored.

    If both `dotenv_path` and `stream` are `None`, `find_dotenv()` is used to find the
    .envrc file.
    """
    if encoding is not None:
        raise NotImplementedError("Use LC_ALL to change the encoding for now.")
    if not interpolate:
        raise NotImplementedError
    if dotenv_path is None:
        if stream is None:
            dotenv_path = find_direnv()
        else:
            raise NotImplementedError(
                "Executing shell commands from a stream is not safe."
            )
    if dotenv_path == "":
        if verbose:
            logger.warning(".envrc file missing. Nothing will be loaded.")
        return {}
    elif not is_allowed(dotenv_path):
        raise PermissionError(f"File {dotenv_path} is not allowed by direnv.")

    env_dict_items = parse_bash_env(direnv_as_stream(find_direnv(dotenv_path)))

    return {
        key: value
        for key, value in env_dict_items
        if key not in ["OLDPWD", "PWD", "SHLVL", "_"] and os.environ.get(key) != value
    }
