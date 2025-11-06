import re
import sys
from pathlib import Path

from . import convert_readme_to_bbcode, nuitka_compile

out_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent / "out"
out_dir.mkdir(exist_ok=True)

markdown_readme = (Path(__file__).parent.parent / "README.md").read_text()
# Remove window examples banner image, since LotroInterface and NexusMods have their
# own place to upload images, and Imgur doesn't work in the UK.
markdown_readme = re.sub(
    r"\!\[OneLauncher window examples\]\(.*\)", "", markdown_readme
)
bbcode_readme = convert_readme_to_bbcode.convert(markdown_readme)
(out_dir / "README_BBCode.txt").write_text(bbcode_readme)

nuitka_compile.main(
    out_dir=out_dir, onefile_mode=sys.platform == "linux", nuitka_deployment_mode=True
)
if sys.platform == "win32":
    from .windows_installer import build_installer

    build_installer.main(
        input_dist_dir=out_dir / nuitka_compile.get_dist_dir_name(), out_dir=out_dir
    )
