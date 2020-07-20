from cx_Freeze import setup, Executable
import OneLauncher.Information as info

# For OS dependent executable name
from platform import system

platform = system()

build_options = {
    "packages": ["OneLauncher.Information", "keyring.backends", "cryptography"],
    "excludes": [],
    "optimize": "2",
    "include_files": [
        "OneLauncher/ui",
        "OneLauncher/certificates",
        "OneLauncher/images",
    ],
}

base = "Win32GUI" if platform == "Windows" else None

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
