import os
import pytest


@pytest.mark.skipif(
    not all(os.getenv(k) for k in ["S3_ENDPOINT", "S3_ACCESS_KEY", "S3_SECRET_KEY", "S3_BUCKET"]),
    reason="S3 credentials not configured"
)
def test_generate_urls():
    from app.storage import generate_upload_url, generate_download_url
    url = generate_upload_url("test/key.txt", "text/plain")
    assert "https://" in url
    url = generate_download_url("test/key.txt")
    assert "https://" in url


def test_storage_import():
    # At minimum the module should import without error
    from app import storage
    assert storage._S3 is None
