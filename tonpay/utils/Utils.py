
def selectables2regex(selectables: list[str]) -> str:
    base_re = '|'.join(selectables)
    return f"^({base_re})$"


isFloat_regex = r'^[-+]?\d*\.?\d+$'