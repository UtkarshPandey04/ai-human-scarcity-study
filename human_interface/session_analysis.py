"""
Utilities for analyzing human participant sessions.

These functions operate on the action records produced by
logging_utils.log_action().
"""


ACTIONS = ["gather", "share", "hoard", "move", "skip", "communicate"]


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


def calculate_deception(action_log):
    """Compute arithmetic deception rate:
    Checks messages where kind == 'claim_stock'.
    If claimed value != resource_before, it is machine-verifiably false.
    """
    total_claims = 0
    deceptive_claims = 0

    for record in action_log:
        meta = record.get("meta") or {}
        claim = meta.get("claim") or {}
        kind = claim.get("kind")
        val = claim.get("value")
        if kind == "claim_stock" and val is not None:
            total_claims += 1
            res_before = record.get("resource_before")
            if res_before is not None and int(val) != int(res_before):
                deceptive_claims += 1

    rate = (deceptive_claims / total_claims * 100.0) if total_claims > 0 else 0.0
    return {
        "deceptive_claims": deceptive_claims,
        "total_claims": total_claims,
        "deception_rate": rate,
    }


def calculate_gini(resources: list[float]) -> float:
    """Calculate the Gini coefficient for a distribution of resources across players.
    Returns 0.0 (perfect equality) to 1.0 (maximal inequality).
    """
    if not resources or len(resources) <= 1:
        return 0.0
    # Shift non-negative if any negative resources (dead agents may be at 0)
    vals = [max(0.0, float(r)) for r in resources]
    n = len(vals)
    total = sum(vals)
    if total == 0:
        return 0.0

    diff_sum = sum(abs(xi - xj) for xi in vals for xj in vals)
    return diff_sum / (2.0 * n * total)


def calculate_latency_stats(action_log):
    """Calculate mean and median decision latency in milliseconds."""
    latencies = []
    for record in action_log:
        meta = record.get("meta") or {}
        lat = meta.get("decision_latency_ms")
        if lat is not None and lat >= 0:
            latencies.append(float(lat))

    if not latencies:
        return {"mean_ms": 0.0, "median_ms": 0.0, "count": 0}

    sorted_lats = sorted(latencies)
    mean_lat = sum(latencies) / len(latencies)
    mid = len(sorted_lats) // 2
    med_lat = (
        sorted_lats[mid]
        if len(sorted_lats) % 2 != 0
        else (sorted_lats[mid - 1] + sorted_lats[mid]) / 2.0
    )
    return {"mean_ms": mean_lat, "median_ms": med_lat, "count": len(latencies)}