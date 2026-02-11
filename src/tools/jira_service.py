from .base_service import BaseAtlassianService

class JiraService(BaseAtlassianService):
    def __init__(self):
        # IMPORTANT: This triggers the BaseAtlassianService's __init__
        # which sets up self.client, self.url, etc.
        super().__init__()
    def create_release_ticket(self, summary: str, description: str, project_key: str = "REL"):
        """Creates a ticket for a new release."""
        fields = {
            'project': {'key': project_key},
            'summary': summary,
            'description': description,
            'issuetype': {'name': 'Task'}
        }
        return self.handle_call(self.client.issue_create, fields=fields)

    def update_release_details(self, ticket_key: str, update_dict: dict):
        """Updates summary or description for an existing release."""
        return self.handle_call(self.client.issue_update, ticket_key, update_dict)

    def transition_release(self, ticket_key: str, status_name: str):
        """Moves a ticket to a new state (e.g., 'In Progress', 'Done')."""
        return self.handle_call(self.client.issue_transition, ticket_key, status_name)

    def get_release_summary(self, ticket_key: str):
        """Fetches the full data of a release ticket."""
        print(f"ticket_key: {ticket_key}")
        return self.handle_call(self.client.issue, ticket_key)