from src.preprocess import normalize_age


def test_normalize_age():
    assert normalize_age("2개월") == 2
    assert normalize_age("12개월") == 12
