from setuptools import setup, find_packages

setup(
    name="uaim-device-adapter",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "fastapi>=0.110.0",
        "uvicorn>=0.28.0",
        "pydantic>=2.6.0",
        "pydantic-settings>=2.0.0",
        "websockets>=12.0",
        "pyyaml>=6.0.1",
        "aiofiles>=23.2.0",
    ],
)

