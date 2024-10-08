import os
import pytest
import sys
import subprocess
import textwrap
from typing import List
from unittest import mock
from zipfile import ZipFile


def walk_to_root(path: str):
    last_dir = None
    current_dir = path
    while last_dir != current_dir:
        yield current_dir
        (parent_dir, _) = os.path.split(current_dir)
        last_dir, current_dir = current_dir, parent_dir


class FileToAdd:
    def __init__(self, content: str, path: str):
        self.content = content
        self.path = path


def setup_zipfile(path, files: List[FileToAdd]):
    zip_file_path = path / "test.zip"
    dirs_init_py_added_to = set()
    with ZipFile(zip_file_path, "w") as zip:
        for f in files:
            zip.writestr(data=f.content, zinfo_or_arcname=f.path)
            for dir in walk_to_root(os.path.dirname(f.path)):
                if dir not in dirs_init_py_added_to:
                    print(os.path.join(dir, "__init__.py"))
                    zip.writestr(
                        data="", zinfo_or_arcname=os.path.join(dir, "__init__.py")
                    )
                    dirs_init_py_added_to.add(dir)
    return zip_file_path


@mock.patch.object(sys, "path", list(sys.path))
def test_load_direnv_gracefully_handles_zip_imports_when_no_env_file(tmp_path):
    zip_file_path = setup_zipfile(
        tmp_path,
        [
            FileToAdd(
                content=textwrap.dedent(
                    """
            from direnv import load_direnv

            load_direnv()
        """
                ),
                path="child1/child2/test.py",
            ),
        ],
    )

    # Should run without an error
    sys.path.append(str(zip_file_path))
    import child1.child2.test  # noqa


def test_load_direnv_outside_zip_file_when_called_in_zipfile(tmp_path):
    zip_file_path = setup_zipfile(
        tmp_path,
        [
            FileToAdd(
                content=textwrap.dedent(
                    """
                    import direnv
                    from unittest import mock
                    with mock.patch('direnv._is_allowed', lambda _: True):
                        direnv.load_direnv()
                    """
                ),
                path="child1/child2/test.py",
            ),
        ],
    )
    dotenv_path = tmp_path / ".envrc"
    dotenv_path.write_bytes(b"export a=b")
    code_path = tmp_path / "code.py"
    sys_path = ":".join(sys.path)
    code_path.write_text(
        textwrap.dedent(
            f"""
        import os
        import sys

        sys.path = '{sys_path}'.split(':')
        sys.path.append("{zip_file_path}")

        import child1.child2.test

        print(os.environ.get('a'))
    """
        )
    )

    result = subprocess.run(
        [sys.executable, '-I', str(code_path)],
        capture_output=True,
        cwd=str(tmp_path),
        env={},
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"{result.stderr}")
    assert result.stdout.strip() == "b"
