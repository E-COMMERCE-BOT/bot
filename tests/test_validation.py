from app.utils.validation import normalize_phone_number


def test_normalize_phone_number() -> None:
    assert normalize_phone_number("89991234567") == "+79991234567"
    assert normalize_phone_number("+48123456789") == "+48123456789"
    assert normalize_phone_number("invalid") is None
