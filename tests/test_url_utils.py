from artifact_radar.url_utils import normalize_url


def test_normalize_strips_utm():
    u = "https://Example.com/path/?utm_source=x&id=1"
    assert normalize_url(u) == "https://example.com/path?id=1"


def test_normalize_trailing_slash():
    assert normalize_url("https://foo.com/bar/") == "https://foo.com/bar"


def test_normalize_none():
    assert normalize_url(None) is None
    assert normalize_url("") is None
