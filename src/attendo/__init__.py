"""
ATTENDO - Advanced Timesheet Tracking and Employee Notification Dashboard Operations

A comprehensive enterprise-grade vendor timesheet management system with AI insights,
automated notifications, and advanced analytics.

Version: 1.0.0
Author: MediaTek Hackathon Team
License: MIT
"""

__version__ = "1.0.0"
__author__ = "MediaTek Hackathon Team"
__email__ = "team@attendo.com"

from .core.application import create_app

__all__ = ["create_app"]
