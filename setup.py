import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="wattro_sync",
    version="0.2.0",
    description="Script collection to sync data from local sources to a wattro node",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/wattro/wattro_sync",
    author="Wattro GmbH",
    author_email="admin@wattro.de",
    packages=setuptools.find_packages(),
    license="MIT License",
    install_requires=["requests", "sendgrid", "simple-term-menu", "pyodbc"],
)
