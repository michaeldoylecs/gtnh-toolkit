"""
Module for storing and accessing command line arguments throughout the application.
"""
from argparse import Namespace
from typing import Optional

# Global variable to store parsed arguments
_args: Optional[Namespace] = None

def set_args(args: Namespace) -> None:
    """
    Store the parsed command line arguments.
    
    Args:
        args: The parsed command line arguments from argparse
    """
    global _args
    _args = args

def get_args() -> Optional[Namespace]:
    """
    Get the stored command line arguments.
    
    Returns:
        The parsed command line arguments or None if not set
    """
    return _args

def is_verbose() -> bool:
    """
    Check if verbose mode is enabled.
    
    Returns:
        True if verbose mode is enabled, False otherwise
    """
    if _args is None:
        return False
    return getattr(_args, 'verbose', False)

def get_factory_config_path() -> Optional[str]:
    """
    Get the file path from command line arguments.
    
    Returns:
        The file path or None if not set
    """
    if _args is None:
        return None
    return getattr(_args, 'factory_config', None)
