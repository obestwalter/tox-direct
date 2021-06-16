from setuptools import setup, find_packages

setup(
    name="tox-direct",
    author="Oliver Bestwalter",
    description="plugin for tox - run everything directly (tox creates no virtual env)",
    version="0.4",
    packages=find_packages("src"),
    package_dir={"": "src"},
    entry_points={"tox": ["direct = tox_direct.hookimpls"]},
    install_requires=["tox>=3.12,<4", "py", "pathlib2"],
    extras_require={"test": ["pytest"], "publish": ["twine"]},
)
