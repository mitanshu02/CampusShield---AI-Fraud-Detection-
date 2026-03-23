def combine_url_scores(
    whois_score: int,
    typosquat_score: int,
    phishtank_score: int,
    keyword_score: int
) -> int:
    """Combines 4 signal scores into one final weighted risk score (0-100)."""

    final = (
        whois_score     * 0.25 +
        typosquat_score * 0.30 +
        phishtank_score * 0.30 +
        keyword_score   * 0.15
    )

    # Round to integer and cap at 100
    return min(round(final), 100)


def get_risk_label(score: int) -> str:
    """Converts a numeric score into a human-readable risk level."""
    if score >= 70:
        return "HIGH"
    elif score >= 40:
        return "MEDIUM"
    else:
        return "SAFE"


def get_risk_colour(score: int) -> str:
    """Returns a colour string for the frontend to use."""
    if score >= 70:
        return "red"
    elif score >= 40:
        return "amber"
    else:
        return "green"