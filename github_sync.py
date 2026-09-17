"""
GitHub -> XP sync.

Polls GitHub's public Events API for one username and turns real,
individual events into XP transactions. Every GitHub event already has
its own unique event ID — that becomes the transaction's
external_event_id, so re-polling the same event twice can never award
XP twice.

Rate-limit note: GitHub's public Events API only returns roughly the
last 90 days of activity, capped at 300 events — that's a GitHub
platform limit, not something this code can work around. Unauthenticated
requests are also limited to 60/hour. Set a GITHUB_TOKEN environment
variable to raise that to 5,000/hour (never hardcode it, never send it
to the browser — it's read server-side only).
"""

import os
import time
import json
import requests
from datetime import datetime
import xp_engine
GITHUB_USERNAME = 'buildwithayushmansingh'
SYNC_INTERVAL_SECONDS = 15 * 60  # don't hit GitHub more often than this

PUSH_EVENT_XP = 15
PR_OPENED_XP = 50
ISSUE_OPENED_XP = 20
ISSUE_CLOSED_XP = 25
REPO_CREATED_XP = 100
DAILY_PUSH_CAP = 3  # max push-events counted per day — discourages spam commits


def _github_headers():
    token = os.environ.get('GITHUB_TOKEN')
    headers = {'Accept': 'application/vnd.github+json'}
    if token:
        headers['Authorization'] = f'token {token}'
    return headers


def _fetch_events():
    url = f'https://api.github.com/users/{GITHUB_USERNAME}/events/public'
    resp = requests.get(url, headers=_github_headers(), timeout=8)
    if resp.status_code != 200:
        return []
    return resp.json()

def _parse_github_time(iso_str):
    """GitHub sends UTC times like '2026-09-15T13:45:22Z' — convert to the
    same naive-UTC format the rest of the ledger already uses."""
    try:
        return datetime.strptime(iso_str, '%Y-%m-%dT%H:%M:%SZ').isoformat()
    except (TypeError, ValueError):
        return None
def sync_github_xp(force=False):
    """Awards XP for real GitHub events since the last sync. Safe to call
    on every request — it no-ops unless SYNC_INTERVAL_SECONDS has passed,
    so it never hammers GitHub's API or burns through the rate limit."""
    last_synced = xp_engine.get_meta('github_last_synced')
    now = time.time()
    if not force and last_synced and (now - float(last_synced)) < SYNC_INTERVAL_SECONDS:
        return  # cache still fresh — skip the network call entirely

    try:
        events = _fetch_events()
    except requests.RequestException:
        return

    for event in events:
        event_id = event.get('id')
        event_type = event.get('type')
        repo_name = event.get('repo', {}).get('name')
        payload = event.get('payload', {})
        event_type = event.get('type')
        repo_name = event.get('repo', {}).get('name')
        payload = event.get('payload', {})
        if not event_id:
            continue

        real_time = _parse_github_time(event.get('created_at'))

        if event_type == 'PushEvent':
            if xp_engine.count_today('github_push') >= DAILY_PUSH_CAP:
                continue
            commits = payload.get('commits', [])
            commit_list = [
                {
                    'sha': (c.get('sha') or '')[:7],
                    'message': (c.get('message') or '').split('\n')[0][:120],
                    'url': f"https://github.com/{repo_name}/commit/{c.get('sha', '')}"
                }
                for c in commits
            ]
            detail = json.dumps({'commits': commit_list, 'repo_url': f'https://github.com/{repo_name}'})
            xp_engine.award_xp(
                source='github', activity_type='github_push',
                description=f'Push to {repo_name}', xp=PUSH_EVENT_XP,
                repository=repo_name, external_event_id=f'gh_{event_id}',
                timestamp=real_time, detail=detail
            )

        elif event_type == 'PullRequestEvent' and payload.get('action') == 'opened':
            pr = payload.get('pull_request', {})
            detail = json.dumps({'title': pr.get('title'), 'url': pr.get('html_url')})
            xp_engine.award_xp(
                source='github', activity_type='github_pr_opened',
                description=f'Pull request opened in {repo_name}', xp=PR_OPENED_XP,
                repository=repo_name, external_event_id=f'gh_{event_id}',
                timestamp=real_time, detail=detail
            )

        elif event_type == 'IssuesEvent' and payload.get('action') == 'opened':
            issue = payload.get('issue', {})
            detail = json.dumps({'title': issue.get('title'), 'url': issue.get('html_url')})
            xp_engine.award_xp(
                source='github', activity_type='github_issue_opened',
                description=f'Issue opened in {repo_name}', xp=ISSUE_OPENED_XP,
                repository=repo_name, external_event_id=f'gh_{event_id}',
                timestamp=real_time, detail=detail
            )

        elif event_type == 'IssuesEvent' and payload.get('action') == 'closed':
            issue = payload.get('issue', {})
            detail = json.dumps({'title': issue.get('title'), 'url': issue.get('html_url')})
            xp_engine.award_xp(
                source='github', activity_type='github_issue_closed',
                description=f'Issue closed in {repo_name}', xp=ISSUE_CLOSED_XP,
                repository=repo_name, external_event_id=f'gh_{event_id}',
                timestamp=real_time, detail=detail
            )

        elif event_type == 'CreateEvent' and payload.get('ref_type') == 'repository':
            detail = json.dumps({'repo_url': f'https://github.com/{repo_name}'})
            xp_engine.award_xp(
                source='github', activity_type='github_repo_created',
                description=f'Repository created: {repo_name}', xp=REPO_CREATED_XP,
                repository=repo_name, external_event_id=f'gh_{event_id}',
                timestamp=real_time, detail=detail
            )

    xp_engine.set_meta('github_last_synced', str(now))
    