# Contributing to OneLauncher

Contributions and questions are always welcome! Here's just a couple of things to keep in mind:

- Remember to search the [GitHub Issues](https://github.com/JuneStepp/OneLauncher/issues) before making a bug report or feature request.
- Please [open an issue](https://github.com/JuneStepp/OneLauncher/issues/new/choose) to discuss changes before creating a pull request.

## Development Install

OneLauncher uses [Poetry](https://python-poetry.org) for dependency management. Run `poetry install` in the root folder of this repository to get everything set up. Once installed, OneLauncher can be started with `poetry run onelauncher`. Alternatively, [Nix can be used](#nix).

### Nix

OneLauncher comes with a [Nix](https://nixos.org/) flake for easily replicating the standard development environment. It can be used with [direnv](https://github.com/direnv/direnv) or the `nix develop` command. Once the development shell is activated, OneLauncher can be started with the `onelauncher` command.

## Building

The build ends up in `start_onelauncher.dist`.

Nuitka can't currently cross-compile, but the InstallBuilder installers can be cross-compiled.

`poetry run python compile.py`

## Translation

OneLauncher uses [Weblate](weblate.org) for translations. You can make an account and contribute translations through their site. See the project page [here](https://hosted.weblate.org/projects/onelauncher/).

## Coding Conventions

All code is strictly type checked with Mypy and both linted and formatted with Ruff. Pytest unit tests are encouraged.

## UI Changes

User interfaces are defined in `.ui` files that can be visually edited in pyside6-designer. You can use the command `onelauncher designer` to launch pyside6-designer with OneLauncher's plugins enabled.

UI files must be compiled into Python to be used in OneLauncher. This can be done with `pyside6-uic src/onelauncher/example_window.ui -o src/onelauncher/ui/example_window_uic.py`, replacing "example_window" with the one being updated.

### QSS Classes

OneLauncher uses a system similar to [Tailwind CSS](https://tailwindcss.com/) for styling UIs responsively.

Here's how it works:

- The [dynamic property](https://doc.qt.io/qt-6/designer-widget-mode.html#dynamic-properties) `qssClass` is added to the widget that needs to be styled. This property should always be of the type `StringList`.
- Each string in `qssClass` is a "class" that will affect the widget's styling. This works by selecting for them in dynamically generated [Qt Style Sheets](https://doc.qt.io/qt-6/stylesheet.html).
- The classes are mainly used to set sizes and margins relative to the system font size. Changes can be previewed live in pyside6-designer.
- See the [Tailwind Docs](https://tailwindcss.com/docs/utility-first) for specific class names. The currently supported types are [padding](https://tailwindcss.com/docs/padding), [margin](https://tailwindcss.com/docs/margin), [width](https://tailwindcss.com/docs/width), [min-width](https://tailwindcss.com/docs/min-width), [max-width](https://tailwindcss.com/docs/max-width), [height](https://tailwindcss.com/docs/height), [min-height](https://tailwindcss.com/docs/min-height), [max-height](https://tailwindcss.com/docs/max-height), [font size](https://tailwindcss.com/docs/font-size), and icon size.
