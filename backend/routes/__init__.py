"""Flask routes for the application."""
from .analysis import analysis_bp
from .analysis_v2 import analysis_v2_bp

__all__ = ["analysis_bp", "analysis_v2_bp"]
