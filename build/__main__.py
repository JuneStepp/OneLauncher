import sys
from pathlib import Path

from . import compile, convert_readme_to_bbcode

out_dir = Path(__file__).parent / "out"
out_dir.mkdir(exist_ok=True)

bbcode_readme = convert_readme_to_bbcode.convert(
    (Path(__file__).parent.parent / "README.md").read_text(),
)
(out_dir / "README_BBCode.txt").write_text(bbcode_readme)

compile.main(
    out_dir=out_dir, onefile_mode=sys.platform == "linux", nuitka_deployment_mode=True
)
if sys.platform == "win32":
    from .windows_installer import build_installer

    build_installer.main(
        input_dist_dir=out_dir / compile.get_dist_dir_name(), out_dir=out_dir
    )
