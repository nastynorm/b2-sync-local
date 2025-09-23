"""
Setup script for B2 Sync Local application
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

# Read requirements
requirements_file = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_file.exists():
    requirements = requirements_file.read_text().strip().split('\n')

setup(
    name="b2-sync-local",
    version="1.0.0",
    author="B2 Sync Developer",
    author_email="developer@b2sync.local",
    description="A Backblaze B2 cloud storage sync application similar to OneDrive",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/b2-sync-local",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: MacOS",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: System :: Archiving :: Backup",
        "Topic :: System :: Filesystems",
        "Topic :: Internet :: File Transfer Protocol (FTP)",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "b2-sync-local=main:main",
        ],
        "gui_scripts": [
            "b2-sync-local-gui=main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.txt", "*.md", "*.ico", "*.png"],
    },
    zip_safe=False,
)