# python-direnv

Python-direnv executes a direnv `.envrc` file and sets its environment
variables. It helps in the development of applications following the
[12-factor](https://12factor.net/) principles.

Contrary to most related projects, python-direnv will not read
key-value pairs, but actually load them in a bash subshell, so you can
use bash commands. This comes with a price (vulnerability to [shell
injection](https://docs.python.org/3/library/subprocess.html#security-considerations))
but not more than using `direnv` itself.

In cases you can avoid that risk, it is recommended to use a safer
approach, see [related projects](#related-projects).

Additionally, this package implements the same public API as python-dotenv.

If a `.envrc` file has not been allowed to execute with `direnv allow`, these functions will fail.

- [Getting Started](#getting-started)
- [Other Use Cases](#other-use-cases)
  * [Load configuration without altering the environment](#load-configuration-without-altering-the-environment)
  * [Load .env files in IPython](#load-env-files-in-ipython)
- [Differences with python-dotenv](#differences-with-python-dotenv)
  * [Streams](#streams)
  * [Command-line interface](#command-line-interface)
  * [Variable expansion](#variable-expansion)
  * [direnv-values](#direnv-values)
- [Related Projects](#related-projects)

## Getting Started

```shell
pip install python-direnv
```

If your application takes its configuration from environment variables, like a 12-factor
application, launching it in development is not very practical because you have to set
those environment variables yourself.

To help you with that, you can add Python-direnv to your application to make it load the
configuration from a `.env` file when it is present (e.g. in development) while remaining
configurable via the environment:

```python
from direnv import load_direnv

load_direnv()  # take environment variables

# Code of your application, which uses environment variables (e.g. from `os.environ` or
# `os.getenv`) as if they came from the actual environment.
```

By default, `load_direnv` doesn't override existing environment variables and looks for a `.envrc` file in same directory as python script or searches for it incrementally higher up.

To configure the development environment, add a bash file named `.envrc` in the root directory of your
project:

```
.
├── .envrc
└── foo.py
```

You will probably want to add `.envrc` to your `.gitignore`, especially if it contains
secrets like a password.

See the section "File format" below for more information about what you can write in a
`.envrc` file.

## Other Use Cases

### Load configuration without altering the environment

The function `direnv_values` works more or less the same way as `load_direnv`, except it
doesn't touch the environment, it just returns a `dict` with the values parsed from the
`.envrc` file.

```python
from direnv import direnv_values

config = direnv_values(".envrc")
```

This notably enables advanced configuration management:

```python
import os
from direnv import direnv_values

config = {
    **direnv_values(".env.shared"),  # load shared development variables
    **direnvvalues(".env.secret"),  # load sensitive variables
    **os.environ,  # override loaded values with environment variables
}
```

### Load .envrc files in IPython

You can use direnv in IPython.  By default, it will use `find_direnv` to search for a
`.envrc` file:

```python
%load_ext direnv
%direnv
```

You can also specify a path:

```python
%direnv relative/or/absolute/path/to/.envrc
```

Optional flags:

- `-o` to override existing variables.
- `-v` for increased verbosity.

## Differences with python-dotenv

### Streams

Contrary to `python-dotenv`, this package doesn't implement
[streams][python_streams] via the `stream` argument of `load_direnv`
and `direnv_values`. This behaviour is unsafe with bash subshells and
doesn't allow to check if you have allowed the file to be
executed. The argument still exists to maintain the API, but will
return a `NotImplementedError`.

### Command-line interface

No command-line interface is implemented.

### Variable expansion

Beware, variable expansion is not working in the same way as in
python-dotenv, but as standard bash. This is mainly what you would
expect :

With `load_direnv(override=True)` or `direnv_values()`, the value of a variable is the
first of the values defined in the following list:

- Value of that variable in the `.envrc` file.
- Value of that variable in the environment.
- Default value, if provided.
- Empty string.

With `load_direnv(override=False)`, the value of a variable is the first of the values
defined in the following list:

- Value of that variable in the environment.
- Value of that variable in the `.envrc` file.
- Default value, if provided.
- Empty string.

There's however a diverging behaviour when using POSIX expansion on an
existing variable, see the test
`test_load_direnv_redefine_var_used_in_file_no_override` for more
information. This will probably continue to diverge, as I think this
version makes more sense.

### direnv-values

The function `direnv-values` doesn't environment variables if they are
already set to the same return value in the current environment. This
is because the dict is constructed from a diff between starting and
finishing environment in the bash subshell.

## Related Projects

-   [python-dotenv](https://github.com/theskumar/python-dotenv) - Dependency and main inspiration
-   [Honcho](https://github.com/nickstenning/honcho) - For managing
    Procfile-based applications.
-   [django-dotenv](https://github.com/jpadilla/django-dotenv)
-   [django-environ](https://github.com/joke2k/django-environ)
-   [django-environ-2](https://github.com/sergeyklay/django-environ-2)
-   [django-configuration](https://github.com/jezdez/django-configurations)
-   [dump-env](https://github.com/sobolevn/dump-env)
-   [environs](https://github.com/sloria/environs)
-   [dynaconf](https://github.com/rochacbruno/dynaconf)
-   [parse_it](https://github.com/naorlivne/parse_it)
-   [python-decouple](https://github.com/HBNetwork/python-decouple)

[python_streams]: https://docs.python.org/3/library/io.html