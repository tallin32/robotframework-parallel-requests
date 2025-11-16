from setuptools import setup, find_packages

setup(
    name="robotframework-parallel-requests",
    version="0.1.0",
    description="Parallelized HTTP Request library for Robot Framework (httpx + ThreadPool MVP)",
    author="",
    packages=find_packages(),
    install_requires=[
        "httpx>=0.23.0",
        "robotframework>=4.0",
        "respx>=0.20.0",
        "pytest>=7.0",
    ],
    python_requires=">=3.8",
)