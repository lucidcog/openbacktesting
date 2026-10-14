"""Versioned access to ordinary workspace files and stable execution snapshots."""

from __future__ import annotations

import json
import os
import shutil
import stat
import tempfile
import threading
from contextlib import contextmanager
from hashlib import sha256
from pathlib import Path

from openbacktesting_studio.protocol import relative_path

EXCLUDED = {
    ".git",
    ".venv",
    "node_modules",
    "__pycache__",
    ".openbacktesting",
    ".pytest_cache",
    ".ruff_cache",
}
TEXT_SUFFIXES = {".py", ".txt", ".md", ".toml", ".json", ".yaml", ".yml", ".csv", ".ini", ".cfg"}


class WorkspaceError(Exception):
    def __init__(self, code, message, status=400, **details):
        super().__init__(message)
        self.code, self.status, self.details = code, status, details


class Workspace:
    def __init__(self, root: Path, max_file_bytes=2 * 1024 * 1024):
        self.root = root.resolve(strict=True)
        if not self.root.is_dir():
            raise ValueError("Workspace must be a directory")
        self.max_file_bytes = max_file_bytes
        self._lock = threading.RLock()

    def path(self, name: str) -> Path:
        try:
            relative_path(name)
        except ValueError as error:
            raise WorkspaceError("PathDenied", str(error), 403) from error
        pieces = Path(name).parts
        if not pieces or set(pieces) & EXCLUDED:
            raise WorkspaceError("PathDenied", "Internal or excluded path", 403)
        path = self.root
        for piece in pieces:
            path = path / piece
            if path.is_symlink():
                raise WorkspaceError("PathDenied", "Symbolic links are not workspace files", 403)
        if not path.resolve().is_relative_to(self.root):
            raise WorkspaceError("PathDenied", "Path escapes workspace", 403)
        return path

    @contextmanager
    def parent_fd(self, name):
        """Anchor each directory lookup; reject symlinks at the OS boundary on POSIX."""
        self.path(name)
        flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
        descriptor = os.open(self.root, flags)
        try:
            for piece in Path(name).parts[:-1]:
                child = os.open(piece, flags, dir_fd=descriptor)
                os.close(descriptor)
                descriptor = child
            yield descriptor, Path(name).name
        finally:
            os.close(descriptor)

    def read_bytes(self, name, *, limit=None):
        self.path(name)
        try:
            with self.parent_fd(name) as (parent, leaf):
                descriptor = os.open(
                    leaf, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | os.O_NONBLOCK, dir_fd=parent
                )
                with os.fdopen(descriptor, "rb") as stream:
                    info = os.fstat(stream.fileno())
                    if not stat.S_ISREG(info.st_mode):
                        raise WorkspaceError("PathDenied", "Only ordinary files are supported", 403)
                    if limit is not None and info.st_size > limit:
                        raise WorkspaceError(
                            "FileTooLarge", "File exceeds the configured size limit", 413
                        )
                    data = stream.read(limit + 1 if limit is not None else -1)
                    if limit is not None and len(data) > limit:
                        raise WorkspaceError(
                            "FileTooLarge", "File exceeds the configured size limit", 413
                        )
                    return data, stat.S_IMODE(info.st_mode)
        except FileNotFoundError as error:
            raise WorkspaceError("FileNotFound", "Workspace file no longer exists", 404) from error
        except OSError as error:
            raise WorkspaceError("FileAccessFailed", str(error), 403) from error

    def read(self, name):
        if Path(name).suffix.lower() not in TEXT_SUFFIXES:
            raise WorkspaceError("UnsupportedFile", "This file type cannot be edited", 422)
        data, _ = self.read_bytes(name, limit=self.max_file_bytes)
        try:
            content = data.decode("utf-8")
            if "\x00" in content:
                raise ValueError("Binary content")
        except (UnicodeError, ValueError) as error:
            raise WorkspaceError(
                "UnsupportedEncoding", "Only UTF-8 text can be edited", 422
            ) from error
        return {"path": name, "content": content, "revision": sha256(data).hexdigest()}

    def save(self, name, base_revision, content):
        data = content.encode("utf-8")
        if len(data) > self.max_file_bytes or "\x00" in content:
            raise WorkspaceError(
                "InvalidContent", "Content is binary or exceeds the size limit", 413
            )
        with self._lock:
            current = self.read(name)
            if current["revision"] != base_revision:
                raise WorkspaceError(
                    "FileConflict", "File changed on disk; review both versions", 409, disk=current
                )
            _, mode = self.read_bytes(name, limit=self.max_file_bytes)
            with self.parent_fd(name) as (parent, leaf):
                temporary = ".studio-save-" + os.urandom(16).hex()
                descriptor = os.open(
                    temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, mode, dir_fd=parent
                )
                try:
                    with os.fdopen(descriptor, "wb") as stream:
                        stream.write(data)
                        stream.flush()
                        os.fchmod(stream.fileno(), mode)
                        os.fsync(stream.fileno())
                    if self.read(name)["revision"] != base_revision:
                        raise WorkspaceError("FileConflict", "File changed during save", 409)
                    os.replace(temporary, leaf, src_dir_fd=parent, dst_dir_fd=parent)
                    os.fsync(parent)
                finally:
                    try:
                        os.unlink(temporary, dir_fd=parent)
                    except FileNotFoundError:
                        pass
            return {"path": name, "content": content, "revision": sha256(data).hexdigest()}

    def list(self):
        paths = []
        for directory, folders, files in os.walk(self.root, followlinks=False):
            folders[:] = sorted(
                folder
                for folder in folders
                if folder not in EXCLUDED and not (Path(directory) / folder).is_symlink()
            )
            for name in sorted(files):
                path = Path(directory) / name
                if (
                    not path.is_symlink()
                    and path.suffix.lower() in TEXT_SUFFIXES
                    and path.is_file()
                ):
                    paths.append(path.relative_to(self.root).as_posix())
        return paths

    def capture(self, source, extra_resources=()):
        """Copy configured source roots, then recheck names and all original contents."""

        def selection():
            selected = set(source.resources) | set(extra_resources) | {source.path}
            for root in source.roots:
                base = self.root if root == "." else self.path(root)
                if not base.is_dir():
                    raise WorkspaceError("PathDenied", "Source root must be a directory", 403)
                for directory, folders, files in os.walk(base, followlinks=False):
                    folders[:] = sorted(
                        folder
                        for folder in folders
                        if folder not in EXCLUDED and not (Path(directory) / folder).is_symlink()
                    )
                    for name in files:
                        if name.endswith(".py"):
                            selected.add((Path(directory) / name).relative_to(self.root).as_posix())
            return sorted(selected)

        names = selection()
        content = {name: self.read_bytes(name)[0] for name in names}
        if sha256(content[source.path]).hexdigest() != source.revision:
            raise WorkspaceError("FileConflict", "Strategy revision changed before capture", 409)
        for name in names:
            if self.read_bytes(name)[0] != content[name]:
                raise WorkspaceError("SnapshotConflict", "A source changed during capture", 409)
        if selection() != names:
            raise WorkspaceError(
                "SnapshotConflict", "The source file set changed during capture", 409
            )
        state = self.root / ".openbacktesting/studio/snapshots"
        # Internal storage must never follow an existing symlink supplied by a workspace.
        current = self.root
        for part in (".openbacktesting", "studio", "snapshots"):
            current = current / part
            if current.is_symlink():
                raise WorkspaceError("PathDenied", "State directory cannot be a link", 403)
            current.mkdir(exist_ok=True)
        target = Path(tempfile.mkdtemp(dir=state))
        try:
            hashes = {}
            for name, data in content.items():
                path = target / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(data)
                hashes[name] = sha256(data).hexdigest()
            identity = sha256(json.dumps(hashes, sort_keys=True).encode()).hexdigest()
            return {
                "directory": str(target),
                "hash": identity,
                "files": hashes,
                "entry": source.path,
                "roots": source.roots,
            }
        except BaseException:
            shutil.rmtree(target)
            raise
