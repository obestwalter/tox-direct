# tox-direct

[tox](https://tox.readthedocs.io) plugin: run tox envs directly in the same interpreter that tox was run in.

`tox-direct` is something that you usually shouldn't need, but that can be handy in certain situations. It is not recommended to use this approach as a normal part of a tox based automation workflow. The fact that tox creates isolated virtual environments for all automation activities is one of the main reasons for its reliability and is the key to unify command line based an CI automation. 

Having said that: life is messy and sometimes you just want to run a certain environment in the host interpreter. For this there is `tox-direct` now.

**TODO: maybe it makes sense to extend this to being able to run in the basepython rather than in the host environment (if they differ). This is not implemented as I have no need for it (yet).**

## installation

    pip install tox-direct

## concept

`tox-direct` is trying to be safe first and should also have the ability to degrade gracefully when `tox-direct` is not installed. To ensure this, no new key in `tox.ini` is introduced. It works purely over env name, command line parameters or environment variables.

To be safe the following activities will be deactivated by default in direct runs:

* package build
* deps installations
* project installation

There are two ways to request envs being run direct mode: **static** and **on request**. The on request variant also provides a **YOLO** option ((you only live once ;)) which means that everything is run in the host interpreter. This will change the host interpreter and is usually only safe and makes sense (or works at all) if tox is run in a virtual environment already.

### static form 
if the testenv name contains the word **direct** it will be run in direct mode if tox-direct is installed. If this is part of a project that is shared you should make sure that this also works as intended if `tox-direct` is not installed (a.k.a. degrades gracefully).

### on request form 

`tox-direct` adds command line arguments and checks environment variables to run arbitrary envs in direct mode.

With `tox-direct installed`:

```text
$ tox --help
[...]

optional arguments:
  --direct        [tox-direct] deactivate venv, packaging and install steps - 
                  run commands directly (can also be achieved by setting
                  TOX_DIRECT) (default: False)
  --direct-yolo   [tox-direct] do everything in host environment that would
                  otherwise happen in an isolated virtual environment 
                  (can also be achieved by setting TOX_DIRECT_YOLO env var
                  (default: False)
```

**WARNING: at the moment `tox-direct` does not consider different basepythons, which means that running environments with different basepythons makes no sense with `tox-direct` at the moment: they would all run in the same environment where tox is installed (effectively doing the same over and over again).**

**NOTE: the YOLO option is called YOLO for a reason in case you run this as root in your system python :).**

## basic example

Let's assume you are working in some virtualenv already which looks like this:

```text
$ which python
~/.virtualenvs/tmp/bin/python

$ pip list
pip list
Package            Version
------------------ -------
filelock           3.0.12 
importlib-metadata 0.18   
packaging          19.0   
pathlib2           2.3.4  
pip                19.1.1 
pluggy             0.12.0 
py                 1.8.0  
pyparsing          2.4.0  
setuptools         41.0.1 
six                1.12.0 
toml               0.10.0 
tox                3.13.1 
tox-direct         0.2.0  
virtualenv         16.6.1 
wheel              0.33.4 
zipp               0.5.1  


$ tox --version
3.13.1 imported from ~/.virtualenvs/tmp/lib/python3.6/site-packages/tox/__init__.py
registered plugins:
    tox-direct-0.2.0 at ~/.virtualenvs/tmp/lib/python3.6/site-packages/tox_direct/hookimpls.py
```

You have a project with a `tox.ini` like this:

```ini
[tox]
; this is the default - put here to be explicit
skipsdist = False

[testenv:direct-action]
; also the default to be explicit
skip_install = False
deps = pytest
commands =
    pip list
    which python

[testenv:normal]
whitelist_externals = which
skip_install = True
commands = which python
```

run tox with higher verbosity to see the info level messages from `tox-direct`:

```text
tox -vvre direct-action
using tox.ini: ~/oss/tox-dev/tplay/tox.ini (pid 14280)
  removing ~/oss/tox-dev/tplay/.tox/log
[tox-direct] won't build a package
[tox-direct] won't install dependencies in 'direct-action'
[tox-direct] won't install project in direct-action
using tox-3.13.1 from ~/.virtualenvs/tmp/lib/python3.6/site-packages/tox/__init__.py (pid 14280)
skipping sdist step
direct-action start: getenv ~/oss/tox-dev/tplay/.tox/direct-action
direct-action cannot reuse: -r flag
direct-action recreate: ~/oss/tox-dev/tplay/.tox/direct-action
[tox-direct] creating no virtual environment - use: ~/.virtualenvs/tmp/bin/python3.6
direct-action finish: getenv ~/oss/tox-dev/tplay/.tox/direct-action after 0.04 seconds
direct-action start: finishvenv 
~/.virtualenvs/tmp/bin/python3.6 (~/.virtualenvs/tmp/bin/python3.6) is {'executable': '~/.virtualenvs/tmp/bin/python3.6', 'name': 'python', 'version_info': [3, 6, 8, 'final', 0], 'version': '3.6.8 (default, Mar  8 2019, 10:42:28) \n[GCC 8.2.1 20181127]', 'is_64': True, 'sysplatform': 'linux'}
direct-action uses ~/.virtualenvs/tmp/bin/python3.6
write config to ~/oss/tox-dev/tplay/.tox/direct-action/.tox-config1 as 'daa272de3ecab6aebf1f8351873eca5d ~/.virtualenvs/tmp/bin/python3.6\n3.13.1 0 0 0'
direct-action finish: finishvenv  after 0.08 seconds
direct-action start: envreport 
setting PATH=~/.virtualenvs/tmp/bin:~/.virtualenvs/tmp/bin:/usr/local/sbin:/usr/local/bin:/usr/bin:/usr/lib/jvm/default/bin:/usr/bin/site_perl:/usr/bin/vendor_perl:/usr/bin/core_perl:~/bin:~/.screenlayout:~/.i3/bin:~/.gem/ruby/2.6.0/bin
[14287] ~/oss/tox-dev/tplay$ ~/.virtualenvs/tmp/bin/python -m pip freeze >.tox/direct-action/log/direct-action-37.log
direct-action finish: envreport  after 0.59 seconds
direct-action installed: filelock==3.0.12,importlib-metadata==0.18,packaging==19.0,pathlib2==2.3.4,pluggy==0.12.0,py==1.8.0,pyparsing==2.4.0,six==1.12.0,test==0.1.0.dev0,toml==0.10.0,tox==3.13.1,tox-direct==0.2.0,virtualenv==16.6.1,zipp==0.5.1
  removing ~/oss/tox-dev/tplay/.tox/direct-action/tmp
direct-action start: run-test-pre 
direct-action run-test-pre: PYTHONHASHSEED='2631343310'
direct-action finish: run-test-pre  after 0.00 seconds
direct-action start: run-test 
direct-action run-test: commands[0] | pip list
setting PATH=~/.virtualenvs/tmp/bin:~/.virtualenvs/tmp/bin:/usr/local/sbin:/usr/local/bin:/usr/bin:/usr/lib/jvm/default/bin:/usr/bin/site_perl:/usr/bin/vendor_perl:/usr/bin/core_perl:~/bin:~/.screenlayout:~/.i3/bin:~/.gem/ruby/2.6.0/bin
[14292] ~/oss/tox-dev/tplay$ ~/.virtualenvs/tmp/bin/pip list
Package            Version
------------------ -------
filelock           3.0.12 
importlib-metadata 0.18   
packaging          19.0   
pathlib2           2.3.4  
pip                19.1.1 
pluggy             0.12.0 
py                 1.8.0  
pyparsing          2.4.0  
setuptools         41.0.1 
six                1.12.0 
toml               0.10.0 
tox                3.13.1 
tox-direct         0.2.0  
virtualenv         16.6.1 
wheel              0.33.4 
zipp               0.5.1  
direct-action run-test: commands[1] | which python
setting PATH=~/.virtualenvs/tmp/bin:~/.virtualenvs/tmp/bin:/usr/local/sbin:/usr/local/bin:/usr/bin:/usr/lib/jvm/default/bin:/usr/bin/site_perl:/usr/bin/vendor_perl:/usr/bin/core_perl:~/bin:~/.screenlayout:~/.i3/bin:~/.gem/ruby/2.6.0/bin
[14297] ~/oss/tox-dev/tplay$ /usr/bin/which python
~/.virtualenvs/tmp/bin/python
direct-action finish: run-test  after 0.59 seconds
direct-action start: run-test-post 
direct-action finish: run-test-post  after 0.00 seconds
_____________________________ summary _______________________________________
  direct-action: commands succeeded
  congratulations :)
```

tox still creates an envdir at `.tox/direct-action` but it does not contain a virutal environment - it is only used for internal bookkeeping and logging. The interpreter used throughout is `~/.virtualenvs/tmp` - the host interpreter that tox was started from.

In simple direct mode (no yolo) nothing will be build, deps and project won't be installed.

**WARNING: if something is installed in the commands this will still happen as commands will be executed without further inspection.** 
