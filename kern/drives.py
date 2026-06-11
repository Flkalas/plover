"""PL-DOS multi-drive manager (S7d)."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from kern.plfs import Plfs
from kern.vfdd import VfddDriver
from plover_vm.memory.vfdd import VfdConfig, VirtualFdd

SECTOR_COUNT = 64


class DriveError(Exception):
    pass


@dataclass
class _MountedVolume:
    fs: Plfs
    img_path: Path
    drive_id: int


@dataclass
class DriveMgr:
    volumes: dict[str, _MountedVolume] = field(default_factory=dict)
    current: str = "A"
    next_id: int = 0

    def prompt(self) -> str:
        return f"{self.current}>"

    def current_fs(self) -> Plfs:
        return self.fs_for(None)

    def fs_for(self, letter: str | None) -> Plfs:
        key = (letter or self.current).upper()
        vol = self.volumes.get(key)
        if vol is None:
            raise DriveError(f"not mounted: {key}")
        return vol.fs

    def drive_id(self, letter: str) -> int | None:
        vol = self.volumes.get(letter.upper())
        return vol.drive_id if vol else None

    def img_path(self, letter: str) -> Path | None:
        vol = self.volumes.get(letter.upper())
        return vol.img_path if vol else None

    def mounted_letters(self) -> list[str]:
        return sorted(self.volumes.keys())

    def mount(self, letter: str, img_path: Path) -> int:
        key = _normalize_letter(letter)
        if key in self.volumes:
            raise DriveError(f"already mounted: {key}")
        img_path.parent.mkdir(parents=True, exist_ok=True)
        dev = VirtualFdd(VfdConfig(path=img_path, sector_count=SECTOR_COUNT))
        drive_id = self.next_id
        self.next_id += 1
        self.volumes[key] = _MountedVolume(fs=Plfs(VfddDriver(dev)), img_path=img_path, drive_id=drive_id)
        if len(self.volumes) == 1:
            self.current = key
        return drive_id

    def mount_formatted(self, letter: str, img_path: Path) -> int:
        drive_id = self.mount(letter, img_path)
        self.fs_for(letter).format()
        return drive_id

    def unmount(self, letter: str) -> None:
        key = _normalize_letter(letter)
        if key == self.current:
            raise DriveError("cannot unmount current drive")
        if key not in self.volumes:
            raise DriveError(f"not mounted: {key}")
        del self.volumes[key]

    def switch(self, letter: str) -> None:
        key = _normalize_letter(letter)
        if key not in self.volumes:
            raise DriveError(f"not mounted: {key}")
        self.current = key

    def copy(self, src: str, dst: str) -> None:
        src_letter, src_name = parse_dos_path(src)
        dst_letter, dst_name = parse_dos_path(dst)
        if not src_name or not dst_name:
            raise DriveError("bad dos path")
        data = self.fs_for(src_letter).read(src_name)
        dst_fs = self.fs_for(dst_letter)
        try:
            dst_fs.delete(dst_name)
        except FileNotFoundError:
            pass
        dst_fs.create(dst_name, data)

    @staticmethod
    def resolve_img_path(root: Path, raw: str) -> Path:
        p = Path(raw)
        if p.is_absolute():
            return p
        direct = root / raw
        if direct.is_file():
            return direct
        return root / "hw" / "fixtures" / "vfdd" / raw


def parse_dos_path(s: str) -> tuple[str | None, str]:
    s = s.strip()
    if not s:
        raise DriveError("bad dos path")
    if ":" in s:
        head, tail = s.split(":", 1)
        if len(head) != 1:
            raise DriveError("bad dos path")
        return _normalize_letter(head), tail
    return None, s


def _normalize_letter(letter: str) -> str:
    key = letter.upper()
    if len(key) != 1 or not key.isalpha():
        raise DriveError(f"bad letter: {letter}")
    return key
