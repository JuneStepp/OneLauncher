import os
import subprocess
import sys
from collections.abc import Iterable
from pathlib import Path

from onelauncher import __about__, resources


def main(
    input_dist_dir: Path | None = None,
    out_dir: Path | None = None,
    extra_args: Iterable[str] = (),
) -> None:
    env = os.environ.copy() | {
        "PRODUCT_NAME": __about__.__title__,
        "AUTHOR": __about__.__author__,
        "VERSION": __about__.version_parsed.base_version,
        "WEBSITE": __about__.__project_url__,
        "ICON_PATH": str(resources.data_dir / "images/OneLauncherIcon.ico"),
        "EXECUTABLE_NAME": f"{__about__.__package__}.exe",
    }
    if input_dist_dir:
        env["DIST_PATH"] = str(input_dist_dir)

    args = ["dotnet", "build", "-c", "Release"]
    if out_dir:
        args.extend(("--output", str(out_dir)))
    args.extend(extra_args)
    subprocess.run(  # noqa: S603
        args,
        env=env,
        cwd=Path(__file__).parent,
        check=True,
    )


if __name__ == "__main__":
    main(extra_args=sys.argv[1:])
