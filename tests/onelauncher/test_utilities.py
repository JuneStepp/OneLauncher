import logging
from pathlib import Path

import pytest
from onelauncher.utilities import CaseInsensitiveAbsolutePath


class TestCaseInsensitiveAbsolutePath:
    def test_case_insensitive_path(self, tmp_path: Path) -> None:
        # These are added to a temp directory. They should not have a root!
        example_paths: list[tuple[str, str]] = [
            ("Example/foO/bar/CAT/bees.txt", "Example/foo/bar/Cat/BEES.TXT"),
            ("doe/roe", "Doe/Roe"),
        ]

        for paths in example_paths:
            # Make real paths to check
            real_path = tmp_path / paths[1]
            real_path.parent.mkdir(parents=True)
            if real_path.suffix:
                real_path.touch()
            else:
                real_path.mkdir()

            assert CaseInsensitiveAbsolutePath(tmp_path / paths[0]) == real_path

    def test_no_matching_path(self, tmp_path: Path) -> None:
        """No changes are made to the path when any part of it can't be found"""
        (tmp_path / "afolder").mkdir()
        test_path = tmp_path / "AFOLDER" / "TOP_SECRET"
        assert (CaseInsensitiveAbsolutePath(test_path)) == (test_path)

    def test_multiple_matches(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """
        Return first found when there are multiple matches of different case than the
        original path.
        """
        (tmp_path / "file").touch()
        (tmp_path / "File").touch()
        assert CaseInsensitiveAbsolutePath(tmp_path / "FILE").name in ["file", "File"]
        assert caplog.record_tuples == [
            (
                "main",
                logging.WARNING,
                "Multiple matches found for case-insensitive path name with no exact "
                "match. Using first one found.",
            )
        ]
        caplog.clear()

    def test_multiple_matches_with_one_exact_match(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Return exact match when there are multiple matches"""
        (tmp_path / "file").touch()
        (tmp_path / "File").touch()
        (tmp_path / "fIlE").touch()
        (tmp_path / "FILE").touch()
        assert CaseInsensitiveAbsolutePath(tmp_path / "fIlE") == tmp_path / "fIlE"
        assert caplog.record_tuples == [
            (
                "main",
                logging.WARNING,
                "Multiple matches found for case-insensitive path name. One exact "
                "match found. Using exact match.",
            )
        ]

    def test_symlink(self, tmp_path: Path) -> None:
        folder = tmp_path / "folder"
        folder.mkdir()
        file = folder / "file"
        file.touch()
        (tmp_path / "EPIC FOLDER").symlink_to(folder, target_is_directory=True)
        assert CaseInsensitiveAbsolutePath(tmp_path / "epic folder" / "FILE").samefile(
            file
        )

    def test_broken_symlink(self, tmp_path: Path) -> None:
        folder = tmp_path / "folder"
        folder.mkdir()
        (tmp_path / "EPIC FOLDER").symlink_to(folder, target_is_directory=True)
        # Remove original folder, so symlink will be broken
        folder.rmdir()
        # Path stays the same, treated just like any other path that can't be found.
        # No error b/c of encountering the broken symlink
        assert (
            CaseInsensitiveAbsolutePath(tmp_path / "epic folder" / "FILE")
            == tmp_path / "epic folder" / "FILE"
        )

    def test_file_in_path(self, tmp_path: Path) -> None:
        """
        Return original path when a match before the final path component
        is a file rather than folder
        """
        (tmp_path / "shhiamsofolder").touch()
        test_path = tmp_path / "shhiamsofolder" / "place"
        assert CaseInsensitiveAbsolutePath(test_path) == test_path

    def test_home(self) -> None:
        assert CaseInsensitiveAbsolutePath.home() == Path.home()

    def test_case_insensitive_glob(self, tmp_path: Path) -> None:
        file_path = tmp_path / "FiLe23.TXT"
        file_path.touch()
        assert (
            next(CaseInsensitiveAbsolutePath(tmp_path).glob("filE*.txt")) == file_path
        )

    def test_case_insensitive_rglob(self, tmp_path: Path) -> None:
        (tmp_path / "folder").mkdir()
        file_path = tmp_path / "folder" / "FiLe24.TXT"
        file_path.touch()
        assert (
            next(CaseInsensitiveAbsolutePath(tmp_path).rglob("filE*.txt")) == file_path
        )

    def test_truediv_returns_case_insensitive_path(self, tmp_path: Path) -> None:
        (tmp_path / "exists").touch()
        assert isinstance(
            (CaseInsensitiveAbsolutePath(tmp_path) / "exists"),
            CaseInsensitiveAbsolutePath,
        )
        assert isinstance(
            (CaseInsensitiveAbsolutePath(tmp_path) / "does_not_exist"),
            CaseInsensitiveAbsolutePath,
        )
