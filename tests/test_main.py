import io
import logging
import os
import pytest
import subprocess
import sys
import textwrap
from unittest import mock

import direnv


def prepare_file_hierarchy(path):
    """
    Create a temporary folder structure like the following:

        test_find_direnv0/
        └── child1
            ├── child2
            │   └── child3
            │       └── child4
            └── .env

    Then try to automatically `find_direnv` starting in `child4`
    """

    leaf = path / "child1" / "child2" / "child3" / "child4"
    leaf.mkdir(parents=True, exist_ok=True)
    return leaf


def test_find_direnv_no_file_raise(tmp_path):
    leaf = prepare_file_hierarchy(tmp_path)
    os.chdir(leaf)

    with pytest.raises(IOError):
        direnv.find_direnv(raise_error_if_not_found=True, usecwd=True)


def test_find_direnv_no_file_no_raise(tmp_path):
    leaf = prepare_file_hierarchy(tmp_path)
    os.chdir(leaf)

    result = direnv.find_direnv(usecwd=True)

    assert result == ""


def test_find_direnv_found(tmp_path):
    leaf = prepare_file_hierarchy(tmp_path)
    os.chdir(leaf)
    dotenv_path = tmp_path / ".envrc"
    dotenv_path.write_bytes(b"TEST=test\n")

    result = direnv.find_direnv(usecwd=True)

    assert result == str(dotenv_path)


@mock.patch.dict(os.environ, {}, clear=True)
def test_load_direnv_existing_file(dotenv_path, direnv_allow):
    dotenv_path.write_text("export a=b")

    result = direnv.load_direnv(dotenv_path)

    assert result is True
    assert os.environ == {"a": "b"}


@mock.patch.dict(os.environ, {"a": "c"}, clear=True)
def test_load_direnv_existing_variable_no_override(dotenv_path, direnv_allow):
    dotenv_path.write_text("export a=b")

    result = direnv.load_direnv(dotenv_path, override=False)

    assert result is True
    assert os.environ == {"a": "c"}


@mock.patch.dict(os.environ, {"a": "c"}, clear=True)
def test_load_direnv_existing_variable_override(dotenv_path, direnv_allow):
    dotenv_path.write_text("export a=b")

    result = direnv.load_direnv(dotenv_path, override=True)

    assert result is True
    assert os.environ == {"a": "b"}


@pytest.mark.skip(reason="Diverging behaviour with python-dotenv")
@mock.patch.dict(os.environ, {"a": "c"}, clear=True)
def test_load_direnv_redefine_var_used_in_file_no_override(dotenv_path, direnv_allow):
    dotenv_path.write_text('export a=b\nexport d="${a}"')

    result = direnv.load_direnv(dotenv_path)

    assert result is True
    # This is diverging from python-dotenv behaviour.
    assert os.environ == {"a": "c", "d": "c"}


@mock.patch.dict(os.environ, {"a": "c"}, clear=True)
def test_load_direnv_redefine_var_used_in_file_with_override(dotenv_path, direnv_allow):
    dotenv_path.write_text('export a=b\nexport d="${a}"')

    result = direnv.load_direnv(dotenv_path, override=True)

    assert result is True
    assert os.environ == {"a": "b", "d": "b"}


@mock.patch.dict(os.environ, {}, clear=True)
def test_load_direnv_string_io(direnv_allow):
    stream = io.StringIO("export a=b")
    with pytest.raises(NotImplementedError) as excinfo:
        direnv.load_direnv(stream=stream)
        assert "not safe" in str(excinfo.value)


@mock.patch.dict(os.environ, {}, clear=True)
def test_load_direnv_file_stream(dotenv_path):
    dotenv_path.write_text("export a=b")
    with dotenv_path.open() as f:
        with pytest.raises(NotImplementedError) as excinfo:
            direnv.load_direnv(stream=f)
            assert "not safe" in str(excinfo.value)


def test_load_direnv_in_current_dir(tmp_path, direnv_allow):
    dotenv_path = tmp_path / ".envrc"
    dotenv_path.write_bytes(b"export a=b")
    code_path = tmp_path / "code.py"
    code_path.write_text(
        textwrap.dedent(
            """
            import direnv
            import os
            from unittest import mock
            with mock.patch('direnv.main.is_allowed', lambda _: True):
                direnv.load_direnv(verbose=True)
                print(os.environ['a'])
    """
        )
    )
    result = subprocess.run(
        [sys.executable, str(code_path)],
        capture_output=True,
        cwd=str(tmp_path),
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"{result.stderr}")
    assert result.stdout.strip() == "b"


def test_direnv_values_file(dotenv_path, direnv_allow):
    dotenv_path.write_text("export a=b")

    result = direnv.direnv_values(dotenv_path)

    assert result == {"a": "b"}


def test_direnv_values_string_io(direnv_allow):
    env, string, interpolate, expected = {"b": "c"}, "a=$b", False, {"a": "$b"}
    with mock.patch.dict(os.environ, env, clear=True):
        stream = io.StringIO(string)
        stream.seek(0)
        with pytest.raises(NotImplementedError) as excinfo:
            direnv.direnv_values(stream=stream, interpolate=interpolate)
            assert "not safe" in str(excinfo.value)


def test_direnv_values_file_stream(dotenv_path, direnv_allow):
    dotenv_path.write_text("export a=b")
    with dotenv_path.open() as f:
        with pytest.raises(NotImplementedError) as excinfo:
            direnv.direnv_values(stream=f)
            assert "not safe" in str(excinfo.value)
