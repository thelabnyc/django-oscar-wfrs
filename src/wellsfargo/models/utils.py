def _max_len(choices):
    """Given a list of char field choices, return the field max length"""
    lengths = [len(choice) for choice, _ in choices]
    return max(lengths)
