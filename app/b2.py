from b2sdk.v2 import B2Api, InMemoryAccountInfo

from app.config import settings

PUBLIC_BASE = "https://hs-platform.s3.us-east-005.backblazeb2.com"

# ponytail: lazy global; authorize once on first use so app imports without B2 creds
_bucket = None


def get_bucket():
    global _bucket
    if _bucket is None:
        info = InMemoryAccountInfo()
        b2 = B2Api(info)
        b2.authorize_account("production", settings.B2_KEY_ID, settings.B2_APP_KEY)
        _bucket = b2.get_bucket_by_name(settings.B2_BUCKET)
    return _bucket