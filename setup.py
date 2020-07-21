from cx_Freeze import setup, Executable
import OneLauncher.Information as info
from platform import system

packages_list = [
    "OneLauncher.Information",
    "keyring.backends",
    "cryptography",
]

platform = system()

if platform == "Windows":
    base = "Win32GUI"
    packages_list.append("win32timezone")
else:
    base = ""

build_options = {
    "packages": packages_list,
    "excludes": [],
    "optimize": "2",
    "include_files": [
        "OneLauncher/ui",
        "OneLauncher/certificates",
        "OneLauncher/images",
    ],
}

executables = [
    Executable("RunOneLauncher", base=base, targetName="OneLauncher-" + platform)
]

setup(
    name="OneLauncher",
    version=info.Version.strip("-Dev"),
    license="GPL-3.0",
    description=info.Description,
    long_description=info.LongDescription,
    author=info.Author,
    author_email=info.Email,
    url=info.repoUrl,
    options={"build_exe": build_options},
    executables=executables,
)
