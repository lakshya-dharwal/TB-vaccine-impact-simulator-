import math

from src.model.predict import _inverse_target


def test_inverse_target_round_trip_for_log_transform():
    original = 123.4
    transformed = math.log1p(original)
    restored = _inverse_target(transformed, {"log_target": True})
    assert math.isclose(restored, original, rel_tol=1e-9)
