import os
import logging
from atlassian import Jira
from dotenv import load_dotenv

#Load env variables from .env file
load_dotenv()

#BaseAtlassianService
class BaseAtlassianService:
    def __init__(self):
        # Configuration from .env
        self.url = os.getenv("JIRA_URL") #JIRA URL to use
        self.username = os.getenv("JIRA_EMAIL") #Email user account
        self.password = os.getenv("JIRA_API_TOKEN") # Atlassian API Token

        if not all([self.url,self.username,self.password]):
            raise ValueError("Missing Atlassian credentials in environment variables. Check .env file.")
        

        # Initialize the underlying client
        self.client = Jira(
            url=self.url,
            username=self.username,
            password=self.password,
            cloud=True
        )

        self.logger = logging.getLogger(self.__class__.__name__)

    def handle_call(self, func, *args, **kwargs):
        """Wrapper to handle errors and log consistently for the AI."""
        try:
            return func(*args, **kwargs)
        except Exception as e:
            self.logger.error(f"API Call Failed: {str(e)}")
            # We return a string so the AI can understand what went wrong
            return {"error": True, "message": str(e)}