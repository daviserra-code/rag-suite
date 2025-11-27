"""
Jira MCP Client Wrapper
Provides async interface to Jira MCP server via HTTP
"""
import os
import httpx
from typing import Dict, List, Optional, Any
import asyncio


class JiraMCPClient:
    """Client for communicating with Jira MCP server"""
    
    def __init__(self, mcp_url: str = None):
        self.mcp_url = mcp_url or os.getenv("JIRA_MCP_URL", "http://jira-mcp:3000/mcp")
        self.timeout = 30.0
        
    async def _call_tool(self, tool_name: str, arguments: Dict = None) -> Dict:
        """Call a Jira MCP tool"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    self.mcp_url,
                    json={
                        "method": "tools/call",
                        "params": {
                            "name": tool_name,
                            "arguments": arguments or {}
                        }
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result.get('result', {})
                else:
                    print(f"Jira MCP error {response.status_code}: {response.text}")
                    return {"error": f"HTTP {response.status_code}"}
                    
        except Exception as e:
            print(f"Error calling Jira MCP tool {tool_name}: {e}")
            return {"error": str(e)}
    
    # Issue Management
    async def get_issue(self, issue_key: str) -> Dict:
        """Get detailed information about an issue"""
        return await self._call_tool("jira_get_issue", {"issueKey": issue_key})
    
    async def search_issues(self, jql: str, fields: List[str] = None, max_results: int = 50) -> Dict:
        """Search issues using JQL"""
        args = {
            "jql": jql,
            "maxResults": max_results
        }
        if fields:
            args["fields"] = fields
        return await self._call_tool("jira_search_issue", args)
    
    async def create_issue(self, project: str, summary: str, issue_type: str = "Bug", 
                          description: str = "", **kwargs) -> Dict:
        """Create a new issue"""
        args = {
            "project": project,
            "summary": summary,
            "issueType": issue_type,
            "description": description,
            **kwargs
        }
        return await self._call_tool("jira_create_issue", args)
    
    async def update_issue(self, issue_key: str, fields: Dict) -> Dict:
        """Update an issue"""
        return await self._call_tool("jira_update_issue", {
            "issueKey": issue_key,
            "fields": fields
        })
    
    async def transition_issue(self, issue_key: str, transition_id: str) -> Dict:
        """Transition an issue to a new status"""
        return await self._call_tool("jira_transition_issue", {
            "issueKey": issue_key,
            "transitionId": transition_id
        })
    
    # Sprint Management
    async def list_sprints(self, board_id: str = None, project_key: str = None, 
                          state: str = "active,future") -> Dict:
        """List sprints for a board or project"""
        args = {"state": state}
        if board_id:
            args["boardId"] = board_id
        if project_key:
            args["projectKey"] = project_key
        return await self._call_tool("jira_list_sprints", args)
    
    async def get_sprint(self, sprint_id: str) -> Dict:
        """Get detailed information about a sprint"""
        return await self._call_tool("jira_get_sprint", {"sprintId": sprint_id})
    
    async def get_active_sprint(self, board_id: str = None, project_key: str = None) -> Dict:
        """Get the currently active sprint"""
        args = {}
        if board_id:
            args["boardId"] = board_id
        if project_key:
            args["projectKey"] = project_key
        return await self._call_tool("jira_get_active_sprint", args)
    
    # Comments
    async def add_comment(self, issue_key: str, comment: str) -> Dict:
        """Add a comment to an issue"""
        return await self._call_tool("jira_add_comment", {
            "issueKey": issue_key,
            "comment": comment
        })
    
    async def get_comments(self, issue_key: str) -> Dict:
        """Get all comments from an issue"""
        return await self._call_tool("jira_get_comments", {"issueKey": issue_key})
    
    # Worklogs
    async def add_worklog(self, issue_key: str, time_spent: str, comment: str = "") -> Dict:
        """Add a worklog entry"""
        return await self._call_tool("jira_add_worklog", {
            "issueKey": issue_key,
            "timeSpent": time_spent,
            "comment": comment
        })
    
    # Development Information
    async def get_development_info(self, issue_key: str) -> Dict:
        """Get branches, PRs, and commits linked to an issue"""
        return await self._call_tool("jira_get_development_information", {
            "issueKey": issue_key
        })
    
    # Issue History
    async def get_issue_history(self, issue_key: str) -> Dict:
        """Get complete change history of an issue"""
        return await self._call_tool("jira_get_issue_history", {"issueKey": issue_key})
    
    # Issue Relationships
    async def get_related_issues(self, issue_key: str) -> Dict:
        """Get issues related to this issue"""
        return await self._call_tool("jira_get_related_issues", {"issueKey": issue_key})
    
    async def link_issues(self, inward_issue: str, outward_issue: str, 
                         link_type: str = "Relates") -> Dict:
        """Create a link between two issues"""
        return await self._call_tool("jira_link_issues", {
            "inwardIssue": inward_issue,
            "outwardIssue": outward_issue,
            "linkType": link_type
        })
    
    # Status Management
    async def list_statuses(self, project_key: str) -> Dict:
        """Get all available statuses for a project"""
        return await self._call_tool("jira_list_statuses", {"projectKey": project_key})


# Singleton instance
_jira_client = None

def get_jira_client() -> JiraMCPClient:
    """Get or create Jira MCP client singleton"""
    global _jira_client
    if _jira_client is None:
        _jira_client = JiraMCPClient()
    return _jira_client
