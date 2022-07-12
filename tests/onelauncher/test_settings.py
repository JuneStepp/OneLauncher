from typing import List, Tuple

from pathlib import Path

from onelauncher import utilities

def test_case_insensitive_path(tmp_path: Path) -> None:
    # These are added to a temp directory. They should not have a root!
    example_paths: List[Tuple[str, str]] = \
        [("Example/foO/bar/CAT/bees.txt", "Example/foo/bar/Cat/BEES.TXT"),
         ("doe/roe", "Doe/Roe")]

    for paths in example_paths:
        # Make real paths to check
        real_path = tmp_path/paths[1]
        real_path.parent.mkdir(parents=True)
        if real_path.suffix:
            real_path.touch()
        else:
            real_path.mkdir()

        assert utilities.CaseInsensitiveAbsolutePath(tmp_path/paths[0]) == real_path