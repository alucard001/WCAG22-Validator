"""
Setup script for WCAG 2.2 Validator.
"""

from setuptools import setup, find_packages
import os

# Read the contents of README file
with open(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name="wcag22-validator",
    version="0.1.0",
    description="A Python library for validating HTML against WCAG 2.2 criteria",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="MiniMax AI",
    author_email="info@example.com",
    url="https://github.com/example/wcag22-validator",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Internet :: WWW/HTTP",
    ],
    python_requires=">=3.7",
    install_requires=[
        "beautifulsoup4>=4.9.0",
        "requests>=2.25.0",
    ],
    extras_require={
        "selenium": ["selenium>=4.0.0"],
        "dev": [
            "pytest>=6.0.0",
            "flake8>=3.9.0",
            "black>=21.5b0",
        ],
    },
    entry_points={
        "console_scripts": [
            "wcag22-validator=wcag22_validator.cli:main",
        ],
    },
)