"""
base class to be inherited by all services
"""


class BaseService:
    def __init__(self):
        pass

    def execute(self, task):
        raise NotImplementedError
