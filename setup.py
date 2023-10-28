from setuptools import setup

with open("requirements.txt", "r") as requirements_file:
    install_requires = [line.strip() for line in requirements_file]


setup(
    name="ssh_track",
    version="0.1",
    description="Track local files and upload them to remote on save/create/remove",
    author="Justin Deschenaux",
    author_email="justin.deschenaux@gmail.com",
    packages=["ssh_track"],
    entry_points={
        "console_scripts": [
            "ssh_track = ssh_track.main:main"
        ]
    },
    install_requires=install_requires,

)
