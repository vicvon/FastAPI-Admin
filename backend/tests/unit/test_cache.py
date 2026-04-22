from core.cache import CacheManager


def _make_cache_manager() -> CacheManager:
    return object.__new__(CacheManager)


def test_cache_json_serialization_roundtrip() -> None:
    manager = _make_cache_manager()
    payload = {"a": 1, "b": ["x", "y"]}

    raw = manager._serialize(payload, encoding="json")
    restored = manager._deserialize(raw, encoding="json")

    assert restored == payload


def test_cache_pickle_serialization_uses_base64_roundtrip() -> None:
    manager = _make_cache_manager()
    payload = {"nested": {"a": 1}, "items": [1, 2, 3]}

    raw = manager._serialize(payload, encoding="pickle")
    restored = manager._deserialize(raw, encoding="pickle")

    assert isinstance(raw, str)
    assert restored == payload


def test_cache_legacy_use_pickle_flag_maps_to_pickle_encoding() -> None:
    manager = _make_cache_manager()

    resolved = manager._resolve_encoding(use_pickle=True, encoding="json")

    assert resolved == "pickle"
