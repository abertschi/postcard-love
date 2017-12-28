from settings import SECRETS_MAP


def is_valid_secret(secret):
    return SECRETS_MAP.get(secret) is not None


def get_priority(secret):
    entry = SECRETS_MAP.get(secret)
    if not entry:
        return 0
    return entry.get('priority') or 0
