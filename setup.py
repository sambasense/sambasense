from setuptools import setup, find_packages

setup(
    name="sambasense",
    version="1.1.1",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "sambasense=sambasense.__main__:main",
        ],
    },
    python_requires=">=3.10",
    install_requires=[
        "PyQt6>=6.5",
    ],
)
