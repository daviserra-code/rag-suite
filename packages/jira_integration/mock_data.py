"""
Mock Jira data for demo/testing purposes
Provides realistic sample data when Jira MCP is not configured
"""
from datetime import datetime, timedelta
from typing import Dict, List


def get_mock_sprint() -> Dict:
    """Get mock active sprint data"""
    today = datetime.now()
    return {
        'sprint': {
            'id': 'mock-sprint-1',
            'name': 'Sprint 24.12 - Production Optimization',
            'state': 'active',
            'startDate': (today - timedelta(days=7)).isoformat(),
            'endDate': (today + timedelta(days=7)).isoformat(),
            'goal': 'Reduce downtime on Line M10 and implement new quality checks'
        }
    }


def get_mock_issues() -> List[Dict]:
    """Get mock sprint issues"""
    today = datetime.now()
    
    return [
        {
            'key': 'SHOP-145',
            'fields': {
                'summary': 'Line M10 - Sinter jamming causing frequent stops',
                'status': {'name': 'In Progress'},
                'priority': {'name': 'High'},
                'issuetype': {'name': 'Bug'},
                'assignee': {'displayName': 'John Smith'},
                'created': (today - timedelta(days=5)).isoformat(),
                'updated': (today - timedelta(hours=2)).isoformat()
            }
        },
        {
            'key': 'SHOP-142',
            'fields': {
                'summary': 'Implement automated OEE alerts for all production lines',
                'status': {'name': 'In Progress'},
                'priority': {'name': 'Medium'},
                'issuetype': {'name': 'Story'},
                'assignee': {'displayName': 'Maria Garcia'},
                'created': (today - timedelta(days=8)).isoformat(),
                'updated': (today - timedelta(hours=5)).isoformat()
            }
        },
        {
            'key': 'SHOP-138',
            'fields': {
                'summary': 'Emergency stop procedure documentation for Line B02',
                'status': {'name': 'Done'},
                'priority': {'name': 'High'},
                'issuetype': {'name': 'Task'},
                'assignee': {'displayName': 'David Chen'},
                'created': (today - timedelta(days=12)).isoformat(),
                'updated': (today - timedelta(days=1)).isoformat()
            }
        },
        {
            'key': 'SHOP-136',
            'fields': {
                'summary': 'Calibrate sensors on Line C03 assembly station',
                'status': {'name': 'Done'},
                'priority': {'name': 'Medium'},
                'issuetype': {'name': 'Task'},
                'assignee': {'displayName': 'Sarah Johnson'},
                'created': (today - timedelta(days=14)).isoformat(),
                'updated': (today - timedelta(days=2)).isoformat()
            }
        },
        {
            'key': 'SHOP-147',
            'fields': {
                'summary': 'Line D01 - Investigate quality issues with connector assembly',
                'status': {'name': 'Blocked'},
                'priority': {'name': 'Highest'},
                'issuetype': {'name': 'Bug'},
                'assignee': {'displayName': 'John Smith'},
                'created': (today - timedelta(days=3)).isoformat(),
                'updated': (today - timedelta(hours=1)).isoformat()
            }
        },
        {
            'key': 'SHOP-144',
            'fields': {
                'summary': 'Update maintenance schedule for SMT line',
                'status': {'name': 'To Do'},
                'priority': {'name': 'Low'},
                'issuetype': {'name': 'Task'},
                'assignee': {'displayName': 'Maria Garcia'},
                'created': (today - timedelta(days=6)).isoformat(),
                'updated': (today - timedelta(days=6)).isoformat()
            }
        },
        {
            'key': 'SHOP-141',
            'fields': {
                'summary': 'Line M10 - Replace worn conveyor belt',
                'status': {'name': 'In Progress'},
                'priority': {'name': 'High'},
                'issuetype': {'name': 'Maintenance'},
                'assignee': {'displayName': 'David Chen'},
                'created': (today - timedelta(days=9)).isoformat(),
                'updated': (today - timedelta(hours=3)).isoformat()
            }
        },
        {
            'key': 'SHOP-139',
            'fields': {
                'summary': 'Upgrade PLC firmware on Line WC01',
                'status': {'name': 'To Do'},
                'priority': {'name': 'Medium'},
                'issuetype': {'name': 'Task'},
                'assignee': {'displayName': 'Sarah Johnson'},
                'created': (today - timedelta(days=11)).isoformat(),
                'updated': (today - timedelta(days=10)).isoformat()
            }
        },
        {
            'key': 'SHOP-137',
            'fields': {
                'summary': 'Install new safety guards on Line B02',
                'status': {'name': 'Done'},
                'priority': {'name': 'High'},
                'issuetype': {'name': 'Safety'},
                'assignee': {'displayName': 'John Smith'},
                'created': (today - timedelta(days=13)).isoformat(),
                'updated': (today - timedelta(days=3)).isoformat()
            }
        },
        {
            'key': 'SHOP-146',
            'fields': {
                'summary': 'Train operators on new quality checklist procedures',
                'status': {'name': 'In Progress'},
                'priority': {'name': 'Medium'},
                'issuetype': {'name': 'Training'},
                'assignee': {'displayName': 'Maria Garcia'},
                'created': (today - timedelta(days=4)).isoformat(),
                'updated': (today - timedelta(hours=6)).isoformat()
            }
        },
        {
            'key': 'SHOP-143',
            'fields': {
                'summary': 'Line C03 - Reduce scrap rate below 2%',
                'status': {'name': 'In Review'},
                'priority': {'name': 'High'},
                'issuetype': {'name': 'Story'},
                'assignee': {'displayName': 'David Chen'},
                'created': (today - timedelta(days=7)).isoformat(),
                'updated': (today - timedelta(hours=4)).isoformat()
            }
        },
        {
            'key': 'SHOP-140',
            'fields': {
                'summary': 'Create dashboard for real-time production monitoring',
                'status': {'name': 'Done'},
                'priority': {'name': 'Medium'},
                'issuetype': {'name': 'Story'},
                'assignee': {'displayName': 'Sarah Johnson'},
                'created': (today - timedelta(days=10)).isoformat(),
                'updated': (today - timedelta(days=1)).isoformat()
            }
        }
    ]


def get_mock_ai_insights() -> Dict:
    """Get mock AI insights"""
    return {
        'patterns': [
            {
                'type': 'Issue Type Trend',
                'insight': 'Bug issues are most common (4 in last 30 days)',
                'severity': 'info'
            },
            {
                'type': 'Priority Alert',
                'insight': 'High priority issues make up 42% of recent tickets',
                'severity': 'warning'
            },
            {
                'type': 'Blocker Alert',
                'insight': '1 blocked issues requiring attention',
                'severity': 'error'
            },
            {
                'type': 'Line Focus',
                'insight': 'Line M10 has the most related issues (3 tickets)',
                'severity': 'info'
            }
        ],
        'blockers': [
            {
                'key': 'SHOP-147',
                'summary': 'Line D01 - Investigate quality issues with connector assembly',
                'age_days': 3
            }
        ],
        'issue_types': {
            'Bug': 4,
            'Task': 4,
            'Story': 3,
            'Maintenance': 1,
            'Safety': 1,
            'Training': 1
        },
        'priorities': {
            'Highest': 1,
            'High': 5,
            'Medium': 5,
            'Low': 1
        }
    }


def calculate_mock_stats(issues: List[Dict]) -> Dict:
    """Calculate statistics from mock issues"""
    stats = {
        'total': len(issues),
        'todo': 0,
        'in_progress': 0,
        'done': 0,
        'blocked': 0
    }
    
    for issue in issues:
        status = issue.get('fields', {}).get('status', {}).get('name', '').lower()
        if 'done' in status or 'closed' in status:
            stats['done'] += 1
        elif 'progress' in status or 'review' in status:
            stats['in_progress'] += 1
        elif 'blocked' in status:
            stats['blocked'] += 1
        else:
            stats['todo'] += 1
    
    return stats


def get_mock_sprint_data() -> Dict:
    """Get complete mock sprint data"""
    issues = get_mock_issues()
    return {
        'sprint': get_mock_sprint()['sprint'],
        'issues': issues,
        'stats': calculate_mock_stats(issues)
    }
