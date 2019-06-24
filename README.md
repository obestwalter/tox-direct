# tox-direct

[tox](https://tox.readthedocs.io) plugin to be able to run commands directly without creating a virtual environments first.

This might seem pointless but if tox is used as a single entry point into all developer workflows this can be useful in certain scenarios - e.g.:
 
* something needs to be done which does not require a virtual environment (because only system commands are run) 
+ something has to run in the same interpreter that is running tox (e.g. testing things inside a docker container where everything is already set up correctly in a dedicated virtual environment)

At the moment there are two ways to run tox envs in direct mode:

1. if the testenv name contains the word "direct"
2. if the environment variable `TOX_DIRECT` is set


minimal example:

```ini
[tox]
skipdist = True

[testenv:direct-action]
skip_install = True
commands = which python

[testenv:something-else]
skip_install = True
commands = which python
```

If I run these in a virtual environment (`.virtualenvs/tmp`) with `tox` and `tox-direct` installed:

```text
$ TOX_DIRECT=1 tox -qre something-else

We need direct action! No virtual environment! Ain't Nobody Got Time for That!
/home/ob/.virtualenvs/tmp/bin/python
_______________________________ summary _______________________________________
  something-else: commands succeeded
  congratulations :)
```

```text
$ tox -qre direct-action  

We need direct action! No virtual environment! Ain't Nobody Got Time for That!
/home/ob/.virtualenvs/tmp/bin/python
_______________________________ summary _______________________________________
  direct-action: commands succeeded
  congratulations :)
```

So everything would be executed (and also installed) directly in that environment.
