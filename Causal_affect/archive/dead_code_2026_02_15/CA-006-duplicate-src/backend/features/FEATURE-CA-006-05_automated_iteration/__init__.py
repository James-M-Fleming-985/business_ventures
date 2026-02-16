"""Automated Iteration Feature Module.

This module provides automated iteration capabilities for continuous improvement
of AI agents through systematic experimentation and optimization.
"""

from typing import TYPE_CHECKING

__version__ = "0.1.0"
__all__ = [
    "IterationService",
    "IterationConfig",
    "IterationStatus",
    "IterationType",
]

if TYPE_CHECKING:
    from .services.iteration_service import IterationService
    from .models.iteration import IterationConfig, IterationStatus, IterationType