from __future__ import print_function
import os
import sys

import py
import tox
from tox.session import reporter
from tox.exception import Error


class DIRECT:
    MARKER = "direct"
    ENV_VAR = "TOX_DIRECT"
    ENV_VAR_YOLO = "TOX_DIRECT_YOLO"
    SKIPSDIST_ORIGINAL = "_TOX_DIRECT_SKIPSDIST_ORIGINAL"
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
    if DIRECT.ENV_VAR in os.environ:
        config.option.direct = True
    if DIRECT.ENV_VAR_YOLO in os.environ:
        config.option.direct_yolo = True
    YOLO = config.option.direct_yolo
    if is_direct_run(config):
        if YOLO:
            reporter.info("YOLO! Do everything in the host environment.")
        setattr(config, DIRECT.SKIPSDIST_ORIGINAL, config.skipsdist)
        if not config.skipsdist and not YOLO:
            reporter.info("[tox-direct] won't build a package")
            config.skipsdist = True
        for name, envconfig in config.envconfigs.items():
            if not is_direct_call(config) and not is_direct_env(name, envconfig):
                continue
            # TODO this could also be basepython on request (needed?)
            envconfig.get_envbindir = lambda: py.path.local(DIRECT.PYTHON.dirname)
            envconfig.get_envpython = lambda: py.path.local(DIRECT.PYTHON)
            assert envconfig.envpython == DIRECT.PYTHON, envconfig.envpython
            if envconfig.deps and not YOLO:
                reporter.info(
                    "[tox-direct] won't install dependencies in '{}'".format(name)
                )
                envconfig.deps = []
            if not envconfig.skip_install and not YOLO:
                envconfig.skip_install = True
                reporter.info("[tox-direct] won't install project in {}".format(name))


@tox.hookimpl
def tox_testenv_create(venv):
    if not is_direct_run(venv.envconfig.config):
        return  # normal behaviour
    isDirectCall = is_direct_call(venv.envconfig.config)
    isDirectEnv = is_direct_env(venv.name, venv.envconfig)
    YOLO = venv.envconfig.config.option.direct_yolo
    if not isDirectEnv and not YOLO:
        # direct run only safe for "normal" env if package not used in testenv
        needsPackage = (
            not venv.envconfig.skip_install
            and not venv.envconfig.usedevelop
        )
        if needsPackage and not getattr(venv.envconfig.config, DIRECT.SKIPSDIST_ORIGINAL):
            raise NormalEnvNeedsPackage(
                "[tox-direct] FATAL: tox env '{}' needs a package.\n"
                "Do not run this env as part of a direct run or "
                "run everything in the host (including package build) by running "
                "with --direct-yolo flag.\n"
                "WARNING: this will change the host environment.".format(venv.name)
            )

    if isDirectCall or isDirectEnv:
        venv.is_allowed_external = lambda _: True  # everything goes!
        reporter.info(
            "[tox-direct] creating no virtual environment - use:"
            " {}".format(venv.envconfig.envpython)
        )
        if not YOLO:
            return True
        reporter.info("[tox-direct] YOLO!1!!")


def is_direct_run(config):
    return is_direct_call(config) or has_direct_envs(config.envconfigs)


def is_direct_call(config):
    return config.option.direct or config.option.direct_yolo


def has_direct_envs(envconfigs):
    return any(is_direct_env(envname, envconfig) for envname, envconfig in envconfigs.items() )


def is_direct_env(envname, envconfig):
    return DIRECT.MARKER in envname or envconfig.direct


class NormalEnvNeedsPackage(Error):
    """Raised when a direct run contains a normal env needing a package."""
