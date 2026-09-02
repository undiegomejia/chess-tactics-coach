import os
from anthropic import Anthropic

class ClaudeCoachAdapter:
    def __init__(self):
        self.client = Anthropic(api_key=os.getenv("CLAUDE_API_KEY"))