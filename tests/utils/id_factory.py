# simple monotonic int generator we can import anywhere
import itertools
_id_counter = itertools.count(start=100)          # avoid colliding with real data


def next_pk() -> int:
    """Return a fresh positive int to use as primary-key in SQLite tests."""
    return next(_id_counter)
