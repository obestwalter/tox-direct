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


class MockEnvConfigDirect:
    direct = True


class MockEnvConfigNormal:
    direct = False


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
    "envconfigs, expectation",
    (
        ({}, False),
        ({"direct":MockEnvConfigNormal}, True),
        ({"direct":MockEnvConfigDirect}, True),
        ({"directwhatever":MockEnvConfigNormal}, True),
        ({"whateverdirect":MockEnvConfigNormal}, True),
        ({"whatdirectever":MockEnvConfigNormal}, True),
        ({"direct":MockEnvConfigNormal,"another-direct":MockEnvConfigNormal}, True),
        ({"normal":MockEnvConfigNormal,"another-normal":MockEnvConfigNormal}, False),
        ({"normal":MockEnvConfigNormal,"another-normal":MockEnvConfigDirect}, True),
    ),
)
def test_has_direct_envs(envconfigs, expectation):
    if isinstance(expectation, bool):
        assert has_direct_envs(envconfigs) == expectation
    else:
        with pytest.raises(expectation):
            has_direct_envs(envconfigs)

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


def test_mixed_run_crashes_when_normal_env_needs_package(cmd, initproj):
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
    r = cmd()
    assert r.ret == 1
    assert "[tox-direct] FATAL: tox env 'normal' needs a package" in r.err


def test_mixed_run_does_not_crash_when_normal_env_needs_no_package(cmd, initproj):
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
    assert "won't build a package" in r.out
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
