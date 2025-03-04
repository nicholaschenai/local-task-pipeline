"""
research on the given topic
"""
from services.base_service import BaseService
from jigsawstack import JigsawStack

class ResearchService(BaseService):
    def __init__(self, api_key):
        self.jigsawstack = JigsawStack(api_key=api_key)

    def execute(self, description):
        result = self.jigsawstack.web.search({
            "query": description,
            "ai_overview": True,
        })
        return result
