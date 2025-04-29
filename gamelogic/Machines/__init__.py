# Update import:
from .Base import MachineRecipe
from gamelogic.GameTime import GameTime # Add this import
from .StandardOverclockMachine import StandardOverclockMachineRecipe
from .PerfectOverclockMachine import PerfectOverclockMachineRecipe

__all__ = [
    'MachineRecipe',
    # Remove 'GameTicks',
    'GameTime', # Add GameTime
    'StandardOverclockMachineRecipe',
    'PerfectOverclockMachineRecipe',
]
