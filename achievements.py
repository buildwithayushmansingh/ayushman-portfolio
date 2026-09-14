"""
Achievement system — auto-unlocks based on real state in the XP ledger.

Nothing here can be granted manually. Every rule reads real transactions
(projects created, GitHub PRs opened, active days, streak) and unlocks
automatically. Each unlock is stored once — checking repeatedly is safe.
"""

import sqlite3
from datetime import datetime, timedelta
import xp_engine

ACHIEVEMENTS = [
    {
        'id': 'first_steps', 'name': 'First Steps',
        'description': 'Earn your first XP.', 'icon': '🌱',
        'xp_reward': 10, 'rarity': 'Common',
        'condition': lambda ctx: ctx['total_xp'] > 0,
    },
    {
        'id': 'builder', 'name': 'Builder',
        'description': 'Create 5 projects.', 'icon': '🚀',
        'xp_reward': 100, 'rarity': 'Rare',
        'condition': lambda ctx: ctx['project_count'] >= 5,
    },
    {
        'id': 'open_source', 'name': 'Open Source',
        'description': 'Open your first pull request.', 'icon': '🐙',
        'xp_reward': 75, 'rarity': 'Rare',
        'condition': lambda ctx: ctx['pr_count'] >= 1,
    },
    {
        'id': 'consistency', 'name': 'Consistency',
        'description': 'Reach a 7-day activity streak.', 'icon': '🔥',
        'xp_reward': 50, 'rarity': 'Rare',
        'condition': lambda ctx: ctx['streak'] >= 7,
    },
    {
        'id': 'dedicated', 'name': 'Dedicated',
        'description': 'Log activity on 30 different days.', 'icon': '💯',
        'xp_reward': 150, 'rarity': 'Epic',
        'condition': lambda ctx: ctx['active_days'] >= 30,
    },
    {
        'id': 'milestone_5000', 'name': 'Milestone',
        'description': 'Reach 5,000 total XP.', 'icon': '🏆',
        'xp_reward': 200, 'rarity': 'Legendary',
        'condition': lambda ctx: ctx['total_xp'] >= 5000,
    },
]


def init_db():
    conn = sqlite3.connect(xp_engine.DB_PATH)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS achievements_unlocked (
            id TEXT PRIMARY KEY,
            unlocked_at TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()


def _unlocked_ids():
    conn = sqlite3.connect(xp_engine.DB_PATH)
    rows = conn.execute('SELECT id FROM achievements_unlocked').fetchall()
    conn.close()
    return {r[0] for r in rows}


def _unlock(achievement):
    conn = sqlite3.connect(xp_engine.DB_PATH)
    try:
        conn.execute(
            'INSERT INTO achievements_unlocked (id, unlocked_at) VALUES (?, ?)',
            (achievement['id'], datetime.utcnow().isoformat())
        )
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return False  # already unlocked — no-op
    conn.close()
    xp_engine.award_xp(
        source='achievement', activity_type='achievement_unlocked',
        description=f"Achievement unlocked: {achievement['name']}",
        xp=achievement['xp_reward'],
        external_event_id=f"achievement_{achievement['id']}"
    )
    return True


def _build_context():
    transactions = xp_engine.get_transactions(limit=1000)
    project_count = len({t['project_id'] for t in transactions
                          if t['activity_type'] == 'project_created' and t['project_id']})
    pr_count = sum(1 for t in transactions if t['activity_type'] == 'github_pr_opened')
    active_dates = sorted({t['timestamp'][:10] for t in transactions})

    # current streak: consecutive days ending today or yesterday (UTC).
    # Note: this is a "portfolio + GitHub activity" streak based on the XP
    # ledger itself, not a literal GitHub-only commit streak.
    streak = 0
    if active_dates:
        date_set = set(active_dates)
        cursor = datetime.utcnow().date()
        if cursor.isoformat() not in date_set:
            cursor -= timedelta(days=1)
        while cursor.isoformat() in date_set:
            streak += 1
            cursor -= timedelta(days=1)

    return {
        'total_xp': xp_engine.get_total_xp(),
        'project_count': project_count,
        'pr_count': pr_count,
        'active_days': len(active_dates),
        'streak': streak,
    }


def check_achievements():
    """Call after any XP-affecting sync. Unlocks whatever newly qualifies —
    safe to call on every request, already-unlocked ones are skipped."""
    ctx = _build_context()
    unlocked = _unlocked_ids()
    newly_unlocked = []
    for achievement in ACHIEVEMENTS:
        if achievement['id'] in unlocked:
            continue
        if achievement['condition'](ctx):
            if _unlock(achievement):
                newly_unlocked.append(achievement)
    return newly_unlocked


def get_all_with_status():
    """For display: every achievement plus whether it's unlocked + when."""
    conn = sqlite3.connect(xp_engine.DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute('SELECT id, unlocked_at FROM achievements_unlocked').fetchall()
    conn.close()
    unlocked_map = {r['id']: r['unlocked_at'] for r in rows}

    result = []
    for a in ACHIEVEMENTS:
        result.append({
            'id': a['id'], 'name': a['name'], 'description': a['description'],
            'icon': a['icon'], 'xp_reward': a['xp_reward'], 'rarity': a['rarity'],
            'unlocked': a['id'] in unlocked_map,
            'unlocked_at': unlocked_map.get(a['id']),
        })
    return result


def get_summary():
    """Quick numbers for the ID card: current streak + total badges earned."""
    ctx = _build_context()
    return {'streak': ctx['streak'], 'badges': len(_unlocked_ids())}


def get_recent_unlocked(limit=3):
    """Most recently unlocked achievements, for the passport back."""
    conn = sqlite3.connect(xp_engine.DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        'SELECT id, unlocked_at FROM achievements_unlocked ORDER BY unlocked_at DESC LIMIT ?',
        (limit,)
    ).fetchall()
    conn.close()
    by_id = {a['id']: a for a in ACHIEVEMENTS}
    return [{**by_id[r['id']], 'unlocked_at': r['unlocked_at']} for r in rows if r['id'] in by_id]
def get_recent_unlocked(limit=5):
    """Most recently unlocked achievements, newest first — for a
    'Recent achievements' widget."""
    unlocked = [a for a in get_all_with_status() if a['unlocked']]
    unlocked.sort(key=lambda a: a['unlocked_at'] or '', reverse=True)
    return unlocked[:limit]