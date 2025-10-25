import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from filelock import FileLock


class JsonStore:
    def __init__(
        self,
        data_dir: Path,
        data_file: str,
        lock_file: str,
        enable_backups: bool = True,
        backup_every_n_writes: int = 50,
    ) -> None:
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.data_path = self.data_dir / data_file
        self.lock_path = self.data_dir / lock_file
        self._lock = asyncio.Lock()
        self._filelock = FileLock(str(self.lock_path))
        self._cache: Dict[str, Any] = {}
        self._last_mtime: float = 0.0
        self._writes = 0
        self._enable_backups = enable_backups
        self._backup_every = max(1, backup_every_n_writes)
        self._ensure_file()

    def _ensure_file(self) -> None:
        if not self.data_path.exists():
            initial = {"version": 1, "books": {}}
            self._sync_write(initial)
        self._sync_load()

    def _sync_load(self) -> None:
        with open(self.data_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self._cache = data
        self._last_mtime = self.data_path.stat().st_mtime

    def _sync_write(self, data: Dict[str, Any]) -> None:
        tmp_path = Path(str(self.data_path) + ".tmp")
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, self.data_path)
        self._last_mtime = self.data_path.stat().st_mtime

    async def _read(self) -> Dict[str, Any]:
        mtime = self.data_path.stat().st_mtime
        if mtime > self._last_mtime:
            # External change detected
            self._sync_load()
        return self._cache

    async def _write(self, data: Dict[str, Any]) -> None:
        # Cross-process lock + in-process lock
        async with self._lock:
            with self._filelock:
                self._sync_write(data)
                self._writes += 1
                if self._enable_backups and (self._writes % self._backup_every == 0):
                    ts = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
                    bak = self.data_dir / f"{self.data_path.name}.bak-{ts}"
                    try:
                        with open(bak, "w", encoding="utf-8") as f:
                            json.dump(data, f, ensure_ascii=False)
                    except Exception:
                        # Best-effort backup
                        pass

    # Public API
    async def health(self) -> Dict[str, Any]:
        return {
            "version": self._cache.get("version", 1),
            "data_file": str(self.data_path),
            "data_file_mtime": self._last_mtime,
        }

    async def get_all(self) -> Dict[str, Any]:
        return await self._read()

    async def replace_all(self, data: Dict[str, Any]) -> None:
        await self._write(data)

    async def upsert_book(self, book_id: str, book_data: Dict[str, Any]) -> None:
        data = await self._read()
        books = data.setdefault("books", {})
        books[book_id] = book_data
        await self._write(data)

    async def delete_book(self, book_id: str) -> bool:
        data = await self._read()
        books = data.get("books", {})
        existed = books.pop(book_id, None) is not None
        if existed:
            await self._write(data)
        return existed

    async def get_book(self, book_id: str) -> Optional[Dict[str, Any]]:
        data = await self._read()
        return data.get("books", {}).get(book_id)

    async def list_books(self) -> Tuple[int, Dict[str, Dict[str, Any]]]:
        data = await self._read()
        books = data.get("books", {})
        return len(books), books
