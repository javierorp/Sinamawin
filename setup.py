"""Application setup"""

from setuptools import setup, find_packages

setup(
    name="Sinamawin",
    version="0.1.0",
    description=("A quick and easy way to manage "
                 "network adapters in Windows (only IPv4)."),
    long_description=open("README.md", encoding="utf-8").read().strip(),
    long_description_content_type="text/markdown",
    author="Javierorp",
    author_email="javierorp@outlook.com",
    url="https://github.com/javierorp/Sinamawin",
    download_url="https://github.com/javierorp/Sinamawin/releases",
    license="GPLv3",
    keywords=[
            "network-adapter",
            "network-interface",
            "ipv4",
            "dhcp"
            "windows",
    ],
    platforms="nt",
    packages=find_packages(),
    install_requires=[
        "pillow==10.2.0",
        "psutil==5.9.7",
        "pyperclip==1.8.2",
        "tk==0.1.0",
        "ttkbootstrap==1.10.1",
    ],
)
