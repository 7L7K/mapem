import logging
from typing import Tuple
from backend.models import Event

 

def primary_participant(event: Event, *, strategy: str = "first") -> Tuple[int, str]:
    """
    Picks a “primary” individual for an Event.

    Args:
        event (Event): SQLAlchemy Event instance.
        strategy (str): Selection approach:
            - "first" : return participants[0]  (default)
            - "named" : return first participant with any non-blank name
            - "with_role:<role>" : e.g. "with_role:bride" (future proof)

    Returns:
        Tuple[int, str]: (individual_id, full_name) or (-1, "Unknown").
    """
    if not event.participants:
        logger.debug(f"No participants for event {event.id}")
        return -1, "Unknown"

    # Strategy router
    if strategy == "first":
        p = event.participants[0]

    elif strategy == "named":
        p = next(
            (ind for ind in event.participants if (ind.first_name or ind.last_name)),  # noqa: E501
            event.participants[0],
        )

    elif strategy.startswith("with_role:"):
        target_role = strategy.split(":", 1)[1]
        p = next(
            (ind for ind in event.participants if getattr(ind, "role", None) == target_role),  # noqa: E501
            event.participants[0],
        )
    else:
        logger.warning(f"Unknown strategy '{strategy}', defaulting to first")
        p = event.participants[0]

    full_name = f"{p.first_name} {p.last_name}".strip() or "Unknown"
    return p.id, full_name
