import os
import pytest
from unittest import mock
from IPython.terminal.embed import InteractiveShellEmbed


@pytest.fixture(autouse=True)
def direnv_allow(monkeypatch):
    monkeypatch.setattr("direnv.main.is_allowed", lambda _: True)


@pytest.fixture
def setup_env(tmp_path, monkeypatch):
    dotenv_file = tmp_path / ".envrc"
    dotenv_file.write_text("export a=b\n")
    os.chdir(tmp_path)
    ipshell = InteractiveShellEmbed()
    ipshell.run_line_magic("load_ext", "direnv")
    yield ipshell


@mock.patch.dict(os.environ, {}, clear=True)
def test_ipython_existing_variable_no_override(setup_env, monkeypatch):
    os.environ["a"] = "c"
    setup_env.run_line_magic("direnv", "")
    assert os.environ == {"a": "c"}


@mock.patch.dict(os.environ, {}, clear=True)
def test_ipython_existing_variable_override(setup_env, monkeypatch):
    os.environ["a"] = "c"
    setup_env.run_line_magic("direnv", "-o")
    assert os.environ == {"a": "b"}


@mock.patch.dict(os.environ, {}, clear=True)
def test_ipython_new_variable(setup_env, monkeypatch):
    setup_env.run_line_magic("direnv", "")
    assert os.environ == {"a": "b"}
