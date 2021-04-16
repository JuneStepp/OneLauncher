from cx_Freeze import setup, Executable
import OneLauncher.Information as info
from platform import system
import PySide6
import os.path


packages_list = [
    "OneLauncher.Information",
    "keyring.backends",
    "cryptography",
    "PySide6.QtXml",
]
zip_include_packages = []

platform = system()

if platform == "Windows":
    base = "Win32GUI"
    packages_list.append("win32timezone")

    plugins_path = os.path.join(PySide6.__path__[0], "plugins")
else:
    base = ""
    plugins_path = os.path.join(PySide6.__path__[0], "Qt", "plugins")
    zip_include_packages += ["PySide6", "PySide6.QtXml", "shiboken6", "encodings"]

build_options = {
    "build_exe": "build",
    "packages": packages_list,
    "excludes": ["tkinter", "unittest", "pydoc", "pdb"],
    "optimize": "2",
    "zip_include_packages": zip_include_packages,
    "include_files": [
        "OneLauncher/ui",
        "OneLauncher/certificates",
        "OneLauncher/images",
        os.path.join(plugins_path, "platforms")
    ],
}

executables = [
    Executable("RunOneLauncher", base=base, target_name="OneLauncher")
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
