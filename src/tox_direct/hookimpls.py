import os

import tox


@tox.hookimpl
def tox_testenv_create(venv, action):
    if "direct" in venv.name or "TOX_DIRECT" in os.environ:
        venv.is_allowed_external = lambda _: True  # everything goes!
        print(
            "We need direct action! "
            "No virtual environment! "
            "Ain't Nobody Got Time for That!"
        )
        return True
