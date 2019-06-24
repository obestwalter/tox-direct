import tox


@tox.hookimpl
def tox_testenv_create(venv, action):
    if "direct" not in venv.name:
        return
    print(
        "We need direct action! No virtual environment! Ain't Nobody Got Time for That!"
    )
    venv.is_allowed_external = lambda _: True  # everything goes!
    return True
