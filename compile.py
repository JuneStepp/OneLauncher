import subprocess
import sys

from onelauncher import __about__

nuitka_arguments = [
    "--standalone",
    # "--static-libpython=yes",
    "--python-flag=-m",  # Package mode. Compile as "pakcage.__main__"
    "--python-flag=isolated",
    "--python-flag=no_docstrings",
    "--warn-unusual-code",
    # f"--include-distribution-metadata={__about__.__package__}",
    "--nofollow-import-to=tkinter,pydoc,pdb,PySide6.QtOpenGL,PySide6.QtOpenGLWidgets,zstandard",
    "--noinclude-setuptools-mode=nofollow",
    "--noinclude-unittest-mode=nofollow",
    "--enable-plugins=pyside6",
    "--include-data-files=src/onelauncher/=onelauncher/=**/*.xsd",
    "--include-data-dir=src/onelauncher/images=onelauncher/images",
    "--include-data-dir=src/onelauncher/locale=onelauncher/locale",
    # Base version, because no strings are allowed.
    f"--product-name={__about__.__title__}",
    f"--product-version={__about__.version_parsed.base_version}",
    f"--file-description={__about__.__title__}",
    f"--copyright={__about__.__copyright__}",
]


def main() -> None:
    if sys.platform == "win32":
        nuitka_arguments.extend(
            [
                "--windows-console-mode=attach",
                "--windows-icon-from-ico=src/onelauncher/images/OneLauncherIcon.ico",
            ]
        )
    elif sys.platform == "darwin":
        nuitka_arguments.extend(
            [
                f"--macos-app-name={__about__.__title__}",
                f"--macos-app-version={__about__.__version__}",
                "--macos-app-icon=src/onelauncher/images/OneLauncherIcon.png",
            ]
        )
    elif sys.platform == "linux":
        nuitka_arguments.extend(
            [
                "--linux-icon=src/onelauncher/images/OneLauncherIcon.png",
            ]
        )
    subprocess.run(
        [sys.executable or "python", "-m", "nuitka", "src/onelauncher"]  # noqa: S603
        + nuitka_arguments
        + sys.argv[1:],
        check=True,
    )


if __name__ == "__main__":
    main()
