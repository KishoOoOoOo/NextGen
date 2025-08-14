#!/usr/bin/env python3
"""
NextGen Hub - Advanced Process Management System
Setup script for installation
"""

from setuptools import setup, find_packages
import os

# Read the README file
def read_readme():
    readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
    if os.path.exists(readme_path):
        with open(readme_path, 'r', encoding='utf-8') as f:
            return f.read()
    return "NextGen Hub - Advanced Process Management System"

# Read requirements
def read_requirements():
    requirements_path = os.path.join(os.path.dirname(__file__), 'backend', 'requirements.txt')
    if os.path.exists(requirements_path):
        with open(requirements_path, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip() and not line.startswith('#')]
    return []

setup(
    name="nextgen-hub",
    version="1.0.0",
    author="NextGen Hub Team",
    author_email="info@nextgenhub.com",
    description="Advanced Process Management System for Windows",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/nextgenhub/nextgen-hub",
    project_urls={
        "Bug Tracker": "https://github.com/nextgenhub/nextgen-hub/issues",
        "Documentation": "https://github.com/nextgenhub/nextgen-hub/wiki",
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: System Administrators",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Microsoft :: Windows",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: System :: Systems Administration",
        "Topic :: System :: Monitoring",
        "Topic :: System :: Distributed Computing",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    keywords="process management, monitoring, windows, system administration, web dashboard",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=22.0.0",
            "flake8>=5.0.0",
            "mypy>=1.0.0",
        ],
        "docs": [
            "mkdocs>=1.4.0",
            "mkdocs-material>=8.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "nextgen-hub=manager.desktop_app:main",
            "nextgen-server=manager.backend.app:run",
        ],
    },
    include_package_data=True,
    package_data={
        "manager": [
            "backend/static/*",
            "backend/static/*/*",
            "data/*.yaml",
            "data/*.example.yaml",
        ],
    },
    data_files=[
        ("share/nextgen-hub", [
            "README.md",
            "LICENSE",
            "CHANGELOG.md",
            "start_orchestratorx.bat",
        ]),
        ("share/nextgen-hub/examples", [
            "data/projects.example.yaml",
        ]),
    ],
    zip_safe=False,
    platforms=["win32"],
    license="MIT",
    license_files=["LICENSE"],
) 