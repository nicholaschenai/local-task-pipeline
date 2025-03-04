"""
BaseInput class is the base class for all input classes.
It contains the common attributes and methods that are used by all input classes.

Inputs to the task management system

contains base methods like retrieving the input data
"""


class BaseInput:
    def __init__(self):
        pass

    def get_input(self):
        raise NotImplementedError
