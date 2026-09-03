"""
Utilities for analyzing human participant sessions.

These functions operate on the action records produced by
logging_utils.log_action().
"""


ACTIONS = ["gather", "share", "hoard", "move", "skip"]


def count_actions(action_log):
    """Return the number of times each action was selected."""

    counts = {action: 0 for action in ACTIONS}

    for record in action_log:
        action = record.get("action_type")

        if action in counts:
            counts[action] += 1

    return counts


def action_rates(action_log):
    """Return the percentage of sessions' actions for each action type."""

    counts = count_actions(action_log)
    total_actions = len(action_log)

    if total_actions == 0:
        return {action: 0.0 for action in ACTIONS}

    return {
        action: (count / total_actions) * 100
        for action, count in counts.items()
    }


def resource_change(action_log):
    """Return the total change in water across the session."""

    if not action_log:
        return 0

    first_resource = action_log[0].get("resource_before", 0)
    final_resource = action_log[-1].get("resource_after", 0)

    return final_resource - first_resource


def get_drought_action(action_log, drought_round):
    """Return the action selected during the drought round."""

    for record in action_log:
        if record.get("round") == drought_round:
            return record.get("action_type")

    return None