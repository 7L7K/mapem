
# File: logging.py
# Created: 2025-04-06 16:00:50
# Edited by: King
# Last Edited: 2025-04-06 16:00:50
# Description: User action logging for tracking decisions and changes.

# logging.py
# logging.py
from backend.models import UserAction
from datetime import datetime

def log_action(session, user_id, action_type, context, decision, tree_id=None):
    """
    Log a user action/decision.
    """
    action = UserAction(
        user_id=user_id,
        action_type=action_type,
        context=context,
        decision=decision,
        tree_id=tree_id,
        timestamp=datetime.utcnow()
    )
    session.add(action)
    session.commit()
