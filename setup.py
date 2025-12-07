"""
Setup script for Adaptive Chess Bot package.
"""
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

with open("requirements.txt", "r", encoding="utf-8") as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith("#")]

setup(
    name="adaptive-chess-bot",
    version="1.0.0",
    author="Student",
    author_email="student@example.com",
    description="An adaptive chess bot that adjusts difficulty based on player skill",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/student/adaptive-chess-bot",
    packages=find_packages(),
    package_data={
        "src": ["stockfish-windows-x86-64-avx2.exe"],
    },
    include_package_data=True,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Education",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Games/Entertainment :: Board Games",
    ],
    python_requires=">=3.10",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "chessbot-api=src.api:main",
            "chessbot-ui=src.app:main",
        ],
    },
)
