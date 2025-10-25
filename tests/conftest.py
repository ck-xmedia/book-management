import os
import shutil
from pathlib import Path

import pytest
from httpx import AsyncClient

from app.main import create_app


@pytest.fixture()
def tmp_data_dir(tmp_path: Path):
    d = tmp_path / "data"
    d.mkdir(parents=True, exist_ok=True)
    # Point app to temp data dir
    os.environ["DATA_DIR"] = str(d)
    os.environ["ENABLE_BACKUPS"] = "false"
    yield d
    # Cleanup
    shutil.rmtree(d, ignore_errors=True)


@pytest.fixture()
async def client(tmp_data_dir):
    app = create_app()
    async with AsyncClient(app=app, base_url="http://test") as c:
        yield c
