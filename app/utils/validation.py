import re

NAME_PATTERN = re.compile(r"^[A-Za-zА-Яа-яЁё-]{2,}$")


def normalize_phone_number(value: str) -> str | None:
    phone = re.sub(r"[^\d+]", "", value)

    if phone.startswith("8") and len(phone) == 11:
        phone = "+7" + phone[1:]
    elif phone.startswith("7") and len(phone) == 11:
        phone = "+" + phone

    if re.fullmatch(r"^\+\d{11,15}$", phone):
        return phone

    return None
