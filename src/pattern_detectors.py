"""
Compatibility wrapper for pattern detector imports.
"""

from patterndetectors import (  # noqa: F401
    detect_cyclic_patterns,
    detect_fan_out,
    detect_fan_in,
    detect_gather_scatter,
    detect_peeling_chains,
    calculate_proximity_score,
)

__all__ = [
    "detect_fan_out",
    "detect_fan_in",
    "detect_gather_scatter",
    "detect_cyclic_patterns",
    "detect_peeling_chains",
    "calculate_proximity_score",
]
