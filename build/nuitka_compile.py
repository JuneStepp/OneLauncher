import subprocess
import sys
from collections.abc import Iterable
from pathlib import Path

from onelauncher import __about__


def get_dist_executable_stem() -> str:
    return __about__.__package__


def get_dist_dir_name() -> str:
    return f"{get_dist_executable_stem()}.dist"


def main(
    out_dir: Path | None = None,
    onefile_mode: bool = False,
    nuitka_deployment_mode: bool = False,
    extra_args: Iterable[str] = (),
) -> None:
    nuitka_arguments = [
        f"--user-package-configuration-file={Path(__file__).parent / 'nuitka_package_config.yml'}",
        f"--output-dir={Path(__file__).parent / 'out'}",
        "--onefile" if onefile_mode else "--standalone",
        "--python-flag=-m",  # Package mode. Compile as "package.__main__"
        "--python-flag=isolated",
        "--python-flag=no_docstrings",
        "--warn-unusual-code",
        "--nofollow-import-to=tkinter,pydoc,pdb,PySide6.QtOpenGL,PySide6.QtOpenGLWidgets,zstandard,asyncio,anyio._backends._asyncio,smtplib,requests,requests_file",
        "--noinclude-setuptools-mode=nofollow",
        "--noinclude-unittest-mode=nofollow",
        "--noinclude-pytest-mode=nofollow",
        "--enable-plugins=pyside6",
        "--include-data-files=src/onelauncher/external/run_ptch_client.exe=onelauncher/external/run_ptch_client.exe",
        "--include-data-files=src/onelauncher/=onelauncher/=**/*.xsd",
        "--include-data-dir=src/onelauncher/images=onelauncher/images",
        "--include-data-dir=src/onelauncher/locale=onelauncher/locale",
        f"--product-name={__about__.__title__}",
        # Base version, because no strings are allowed.
        f"--product-version={__about__.version_parsed.base_version}",
        f"--file-description={__about__.__title__}",
        f"--copyright={__about__.__copyright__}",
    ]
    if out_dir:
        nuitka_arguments.append(f"--output-dir={out_dir}")
    if nuitka_deployment_mode:
        nuitka_arguments.append("--deployment")
    if sys.platform != "win32":
        # Can't use static libpython on Windows currently as far as I know
        nuitka_arguments.append("--static-libpython=yes")
    if sys.platform == "win32":
        nuitka_arguments.extend(
            [
                "--assume-yes-for-downloads",
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
                # To not conflict with the `onelauncher` folder.
                f"--output-filename={__about__.__title__.lower()}.bin",
                "--macos-create-app-bundle",
            ]
        )
    elif sys.platform == "linux":
        nuitka_arguments.extend(
            [
                "--linux-icon=src/onelauncher/images/OneLauncherIcon.png",
            ]
        )
    subprocess.run(  # noqa: S603
        [
            sys.executable or "python",
            "-m",
            "nuitka",
            f"src/{__about__.__package__}",
            *nuitka_arguments,
            *extra_args,
        ],
        check=True,
    )


if __name__ == "__main__":
    main(extra_args=sys.argv[1:])
