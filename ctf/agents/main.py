"""
Main entry point for ADK web interface
This file contains the main coordinator agent that ADK web will discover
"""

from .coordinator import ctf_coordinator

# Export the main coordinator agent for ADK web discovery
__all__ = ["ctf_coordinator"]
