import os
import dotenv
from dotenv.main import DotEnv
import subprocess
from pathlib import Path
import hashlib
import io
import sys
from typing import IO, Dict, Iterable, Iterator, Mapping, Optional, Tuple, Union

# A type alias for a string path to be used for the paths in this file.
# These paths may flow to `open()` and `shutil.move()`; `shutil.move()`
# only accepts string paths, not byte paths or file descriptors. See
# https://github.com/python/typeshed/pull/6832.
StrPath = Union[str, "os.PathLike[str]"]


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


def direnv_as_stream(path):
    """
    Sources the .envrc file, output environment as a stream.
    """
    file_path = os.path.abspath(path)
    wd = os.path.dirname(file_path)
    result = subprocess.run(
        f"cd {wd} 2>&1 && source {file_path} 2>&1 && env",
        shell=True,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Failed to source {path}: {result.stderr}")
    return io.StringIO(result.stdout)


def find_direnv(
    filename: str = ".envrc",
    raise_error_if_not_found: bool = False,
    usecwd: bool = False,
) -> str:
    """
    Search in increasingly higher folders for the given file

    Returns path to the file if found, or an empty string otherwise
    """

    result = dotenv.find_dotenv(filename, raise_error_if_not_found, usecwd)
    if result != "":
        return result
    return dotenv.find_dotenv(
        raise_error_if_not_found=raise_error_if_not_found, usecwd=usecwd
    )


def load_direnv(
    dotenv_path: Optional[StrPath] = None,
    stream: Optional[IO[str]] = None,
    verbose: bool = False,
    override: bool = False,
    interpolate: bool = True,
    encoding: Optional[str] = "utf-8",
) -> bool:
    """Parse a .envrc file and then load all the variables found as environment variables.

    Parameters:
        dotenv_path: Absolute or relative path to .envrc file.
        stream: Text stream (such as `io.StringIO`) with .envrc content, used if
            `dotenv_path` is `None`.
        verbose: Whether to output a warning the .envrc file is missing.
        override: Whether to override the system environment variables with the variables
            from the `.envrc` file.
        encoding: Encoding to be used to read the file.
    Returns:
        Bool: True if at least one environment variable is set else False

    If both `dotenv_path` and `stream` are `None`, `find_dotenv()` is used to find the
    .envrc file with it's default parameters. If you need to change the default parameters
    of `find_dotenv()`, you can explicitly call `find_dotenv()` and pass the result
    to this function as `dotenv_path`.
    """
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
    encoding: Optional[str] = "utf-8",
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
        encoding: Encoding to be used to read the file.

    If both `dotenv_path` and `stream` are `None`, `find_dotenv()` is used to find the
    .envrc file.
    """
    if dotenv_path is None:
        if stream is None:
            dotenv_path = find_direnv()
        else:
            raise NotImplementedError(
                "Executing shell commands from a stream is not safe."
            )
    if dotenv_path == "":
        return {}
    elif not is_allowed(dotenv_path):
        raise PermissionError(f"File {dotenv_path} is not allowed by direnv.")

    env_dict = DotEnv(
        dotenv_path=None,
        stream=direnv_as_stream(find_direnv(dotenv_path)),
        verbose=verbose,
        interpolate=interpolate,
        override=True,
        encoding=encoding,
    ).dict()

    return {
        key: value
        for key, value in env_dict.items()
        if key not in ["OLDPWD", "PWD", "SHLVL", "_"] and os.environ.get(key) != value
    }
