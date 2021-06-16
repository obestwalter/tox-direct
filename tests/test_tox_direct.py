import os
import sys
from textwrap import dedent

import pytest
from tox.config import parseconfig
from tox_direct.hookimpls import has_direct_envs

try:
    from pathlib import Path
except ImportError:
    from pathlib2 import Path


class MockEnvConfig:
    def __init__(self, envname):
        self.envname = envname


class MockEnvConfigDirect(MockEnvConfig):
    direct = True
    direct_yolo = False


class MockEnvConfigYolo(MockEnvConfig):
    direct = False
    direct_yolo = True


class MockEnvConfigNormal(MockEnvConfig):
    direct = False
    direct_yolo = False


class TestArgs:
    def test_normal(self, newconfig):
        newconfig("")
        print(os.getcwd())
        config = parseconfig([])
        assert not config.option.direct
        assert not config.option.direct_yolo

    def test_direct(self, newconfig):
        newconfig("")
        config = parseconfig(["--direct"])
        assert config.option.direct
        assert not config.option.direct_yolo

    def test_direct_yolo(self, newconfig):
        newconfig("")
        config = parseconfig(["--direct-yolo"])
        assert not config.option.direct
        assert config.option.direct_yolo


@pytest.mark.parametrize(
    "envlist, envconfigs, expectation",
    (
        ([],{}, False),
        (["direct"], {"direct": MockEnvConfigNormal("direct")}, True),
        (["direct"], {"direct": MockEnvConfigDirect("direct")}, True),
        (
            ["directwhatever"],
            {"directwhatever": MockEnvConfigNormal("directwhatever")},
            True
        ),
        (
            ["whateverdirect"],
            {"whateverdirect": MockEnvConfigNormal("whateverdirect")},
            True
        ),
        (
            ["whatdirectever"],
            {"whatdirectever": MockEnvConfigNormal("whatdirectever")},
            True
        ),
        (
            ["direct", "another-direct"],
            {
                "direct": MockEnvConfigNormal("direct"),
                "another-direct": MockEnvConfigNormal("another-direct")},
            True
            ),
        (
            ["normal", "another-normal"],
            {
                "normal": MockEnvConfigNormal("normal"),
                "another-normal": MockEnvConfigNormal("another-normal")
            },
            False
        ),
        (
            ["normal", "another-normal"],
            {
                "normal": MockEnvConfigNormal("normal"),
                "another-normal": MockEnvConfigDirect("another-normal")
            },
            True
        ),
    ),
)
def test_has_direct_envs(envlist, envconfigs, expectation):
    if isinstance(expectation, bool):
        assert has_direct_envs(envlist, envconfigs) == expectation
    else:
        with pytest.raises(expectation):
            has_direct_envs(envlist, envconfigs)

@pytest.mark.parametrize("config_sub_string,expected_envname",(
    ("[testenv:direct]", "direct"),
    ("[testenv:normal]\ndirect = True", "normal")
))
def test_config(newconfig, config_sub_string,expected_envname):
    config = newconfig(
        dedent(
        """
        [tox]
        skip_install = True
        {config_sub_string}
        skip_install = True
        deps = a
        """
        ).format(config_sub_string=config_sub_string)
    )
    direct = config.envconfigs[expected_envname]
    assert direct.deps == []
    assert direct.skip_install is True
    assert direct.basepython == sys.executable
    assert direct.envpython == sys.executable
    assert direct.get_envbindir() == str(Path(sys.executable).parent)


def test_does_not_interfere_with_single_normal_env(cmd, initproj):
    initproj(
        "does_not_interfer_with_normal_operation",
        filedefs={
            "tox.ini": """
                    [testenv:normal]
                    deps = decorator
                    commands =
                        pip list
                        python -c 'import sys; print(sys.executable);'
            """
        },
    )
    r = cmd()
    assert r.ret == 0
    assert not r.session.config.option.direct
    assert not r.session.config.option.direct_yolo
    assert "We need direct action" not in r.out
    assert "won't build a package" not in r.out
    assert "won't install dependencies" not in r.out
    assert "won't install project" not in r.out
    assert "decorator" in r.out
    assert "congratulations :)" in r.out
    assert sys.executable not in r.out


def test_mixed_config_when_only_normal_env_is_requested(cmd, initproj):
    projectName = "example_project-1.3"
    initproj(
        projectName,
        filedefs={
            "tox.ini": """
                    [testenv:direct]
                    deps = decorator
                    commands =
                        pip list
                        python -c 'import sys; print(sys.executable);'

                    [testenv:normal]
                    deps = decorator
                    commands =
                        pip list
                        python -c 'import sys; print(sys.executable);'
            """
        },
    )
    r = cmd("tox", "-e", "normal")
    assert r.ret == 0
    assert "example-project 1.3" in r.out


def test_mixed_run_when_normal_env_needs_no_package(cmd, initproj):
    projectName = "example_project-1.3"
    initproj(
        projectName,
        filedefs={
            "tox.ini": """
                    [testenv:direct]
                    deps = decorator
                    commands =
                        pip list
                        python -c 'import sys; print(sys.executable);'

                    [testenv:normal]
                    usedevelop = True
                    deps = decorator
                    commands =
                        pip list
                        python -c 'import sys; print(sys.executable);'
            """
        },
    )
    r = cmd()
    assert r.ret == 0
    assert "example-project 1.3" in r.out


def test_direct_vertical(cmd, initproj):
    initproj(
        "direct_vertical",
        filedefs={
            "tox.ini": """
                    [testenv:direct]
                    deps = dontcare
                    commands = python -c 'import sys; print(sys.executable);'
            """
        },
    )
    r = cmd("tox", "-vv")
    assert r.ret == 0
    assert not r.session.config.option.direct
    assert not r.session.config.option.direct_yolo
    assert "won't build a package" not in r.out
    assert "won't install dependencies" in r.out
    assert "won't install project" in r.out
    assert "creating no virtual environment" in r.out
    assert "congratulations :)" in r.out
    assert sys.executable in r.out


def test_direct_yolo_normal_vertical(cmd, initproj):
    initproj(
        "yolo_normal_vertical",
        filedefs={
            "tox.ini": """
                    [testenv:normal]
                    deps = decorator
                    commands =
                        pip list
                        python -c 'import sys; print(sys.executable);'

            """
        },
    )
    r = cmd("tox", "-vv", "--direct-yolo")
    r.out = "\n".join(r.outlines)
    assert "YOLO!1!!" in r.out
    assert "decorator" in r.out
    assert sys.executable in r.out
    package = list((Path(".tox") / "dist").glob("*"))[0]
    assert "yolo_normal_vertical-0.1.zip" in package.name
