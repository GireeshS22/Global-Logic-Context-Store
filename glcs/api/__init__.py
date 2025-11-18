"""
GLCS API Package.

This package provides a REST API for the Global Logical Context Store.

Usage:
    # Run the API server
    uvicorn glcs.api.app:app --reload

    # Or import the app
    from glcs.api import app

Author: GLCS PhD Research Team
Version: 2.1.0 (Stage 2.1)
"""

from glcs.api.app import app

__all__ = ['app']
