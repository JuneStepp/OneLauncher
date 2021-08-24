import os

nuitka_arguments = ["--standalone",
                    "--assume-yes-for-downloads",
                    "--nofollow-import-to=tkinter,unittest,pydoc,pdb",
                    "--plugin-enable=pyside6",
                    "--include-package keyring.backends",
                    "--include-data-dir src/onelauncher/certificates=onelauncher/certificates",
                    "--include-data-dir src/onelauncher/images=onelauncher/images",
                    "--include-data-dir src/onelauncher/locale=onelauncher/locale",
                    "--include-data-dir src/onelauncher/fonts=onelauncher/fonts",]

def main():
    if os.name == "nt":
        nuitka_arguments.extend(["--windows-disable-console",
                                 "--include-package win32timezone",
                                 "--include-package platformdirs.windows",
                                 "--windows-icon-from-ico=src/onelauncher/images/OneLauncherIcon.ico"])
    elif os.name == "mac":
        nuitka_arguments.extend(["--include-package platformdirs.macos",])
    else:
        nuitka_arguments.extend(["--include-qt-plugins=wayland-shell-integration,platforms",
                                 "--include-package platformdirs.unix",])

    os.system(f"poetry run python -m nuitka {' '.join(nuitka_arguments)} start_onelauncher")

if __name__ == "__main__":
    main()
