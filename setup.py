from cx_Freeze import setup, Executable

# Get program version from OneLauncher/Information.py
from OneLauncher.Information import Version

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
    version=Version,
    description="The OneLauncher for LOTRO and DDO",
    options={"build_exe": build_options},
    executables=executables,
)
