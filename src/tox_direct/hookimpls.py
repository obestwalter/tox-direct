from __future__ import print_function
import os
import sys

import py
import tox
from tox.session import reporter


class DIRECT:
    MARKER = "direct"
    ENV_VAR = "TOX_DIRECT"
    ENV_VAR_YOLO = "TOX_DIRECT_YOLO"
    PYTHON = py.path.local(sys.executable)


@tox.hookimpl
def tox_addoption(parser):
    # necessary to allow the direct= directives in testenv sections
    parser.add_testenv_attribute(
        name="direct",
        type="bool",
        help="[tox-direct] deactivate venv, packaging and install steps - "
        "run commands directly ",
        default=False,
    )
    parser.add_argument(
        "--direct",
        action="store_true",
        help="[tox-direct] deactivate venv, packaging and install steps - "
        "run commands directly "
        "(can also be achieved by setting {})".format(DIRECT.ENV_VAR),
    )
    parser.add_argument(
        "--direct-yolo",
        action="store_true",
        help="[tox-direct] do everything in host environment that would otherwise "
        "happen in an isolated virtual environment (can also be achieved "
        "by setting {} env var".format(DIRECT.ENV_VAR_YOLO),
    )


@tox.hookimpl
def tox_configure(config):
    populate_option_from_env(config.option)
    if not is_direct_run(config.option, config.envlist, config.envconfigs):
        return  # normal behaviour

    yolo = config.option.direct_yolo
    if yolo:
        reporter.info("YOLO! Do everything in the host environment.")

    if safe_to_skipsdist(config.envlist, config.envconfigs):
        if not config.skipsdist:
            reporter.info("[tox-direct] safe to skip sdist - no env needs a package")
        config.skipsdist = True

    for envconfig in config.envconfigs.values():
        if is_direct_call(config) or is_direct_env(envconfig):
            # TODO this could also be basepython on request (needed?)
            envconfig.get_envbindir = lambda: py.path.local(DIRECT.PYTHON.dirname)
            envconfig.get_envpython = lambda: py.path.local(DIRECT.PYTHON)
            assert envconfig.envpython == DIRECT.PYTHON, envconfig.envpython
            if envconfig.deps and not yolo:
                envconfig.deps = []
                reporter.info(
                    "[tox-direct] won't install dependencies in '{}'".format(
                        envconfig.name
                    )
                )
            if not envconfig.skip_install and not yolo:
                envconfig.skip_install = True
                reporter.info(
                    "[tox-direct] won't install project in {}".format(envconfig.name)
                )


@tox.hookimpl
def tox_testenv_create(venv):
    envconfig = venv.envconfig  # configuration for this venv
    option = envconfig.config.option  # command line options
    envlist = envconfig.config.envlist  # names of all used envs in this testrun

    if not is_direct_run(option, envlist, envconfig.config.envconfigs):
        return  # normal behaviour

    if is_direct_call(option) or is_direct_env(envconfig):
        venv.is_allowed_external = lambda _: True  # everything goes!
        reporter.info(
            "[tox-direct] creating no virtual environment - use:"
            " {}".format(envconfig.envpython)
        )
        if not option.direct_yolo:
            return True

        reporter.info("[tox-direct] YOLO!1!!")


def populate_option_from_env(option):
    """If someone requested via anv: adjust command line option accordingly."""
    option.direct = True if os.getenv(DIRECT.ENV_VAR) else False
    option.direct_yolo = True if os.getenv(DIRECT.ENV_VAR_YOLO) else False


def is_direct_run(option, envlist, envconfigs):
    """It's a direct run if requested or one of the env is a direct env."""
    return is_direct_call(option) or has_direct_envs(envlist, envconfigs)


def is_direct_call(option):
    """It's a direct call, if one of the direct options is set."""
    return option.direct or option.direct_yolo


def has_direct_envs(envlist, envconfigs):
    """Has direct envs if any of the envs in this testrun are direct."""
    for envconfig in get_this_runs_envconfigs(envlist, envconfigs):
        if is_direct_env(envconfig):
            return True

        return False


def is_direct_env(envconfig):
    """It's a direct env if requested via env name or testenv attribute."""
    return DIRECT.MARKER in envconfig.envname or envconfig.direct


def safe_to_skipsdist(envlist, envconfigs):
    """If none of the envs in this run need a package: return True."""
    for envconfig in get_this_runs_envconfigs(envlist, envconfigs):
        if envconfig.direct:
            continue  # skip_install will be overridden to True

        if envconfig.skip_install:
            continue  # package never needed - will not be installed

        # package needed if installation is not develop install
        if not envconfig.usedevelop:
            return False

    return True


def get_this_runs_envconfigs(envlist, envconfigs):
    """Filter configs that are requested in this testrun."""
    filtered_envconfigs = []
    for envname in envlist:
        envconfig = envconfigs.get(envname)
        if envconfig:
            filtered_envconfigs.append(envconfig)
    return filtered_envconfigs
