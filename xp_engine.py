"""
Developer XP Engine — single source of truth for XP, level and title.

XP lives in a local SQLite database (data/xp.db). Nothing here is
editable from the frontend or the client — every number the templates
show is computed from real, persisted transactions. Re-running the seed
function is always safe: each seeded event has a fixed external_event_id,
so it can only ever award XP once.
"""

import sqlite3
import os
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'xp.db')

# ---- configurable XP rules — safe to tune, never hardcoded elsewhere ----
PROJECT_CREATED_XP = 100
CERTIFICATE_ADDED_XP = 50

# ---- configurable level curve: XP needed to go from level N-1 to level N ----
def _xp_for_level(n):
    return 100 + (n - 1) * 40

TITLES = [
    (1, 4, 'Explorer'),
    (5, 9, 'Builder'),
    (10, 19, 'Developer'),
    (20, 29, 'Full Stack'),
    (30, 39, 'Engineer'),
    (40, 49, 'Elite Developer'),
    (50, 9999, 'Legend'),
]

# card visual tier — drives which CSS treatment the Developer ID card gets
TIERS = [
    (1, 4, 'explorer'),
    (5, 9, 'builder'),
    (10, 19, 'developer'),
    (20, 29, 'fullstack'),
    (30, 39, 'elite'),
    (40, 9999, 'legend'),
]

JOURNEY_CHECKPOINTS = [1, 5, 10, 20, 30, 40, 50]


def _tier_for_level(level):
    for lo, hi, tier in TIERS:
        if lo <= level <= hi:
            return tier
    return 'legend'


def _journey_data(level):
    n = len(JOURNEY_CHECKPOINTS)
    checkpoints = []
    for i, cp_level in enumerate(JOURNEY_CHECKPOINTS):
        checkpoints.append({
            'level': cp_level,
            'position': round(i / (n - 1) * 100, 1),
            'reached': level >= cp_level,
        })
    if level <= JOURNEY_CHECKPOINTS[0]:
        percent = 0.0
    elif level >= JOURNEY_CHECKPOINTS[-1]:
        percent = 100.0
    else:
        percent = 0.0
        for i in range(n - 1):
            lo, hi = JOURNEY_CHECKPOINTS[i], JOURNEY_CHECKPOINTS[i + 1]
            if lo <= level <= hi:
                seg = (level - lo) / (hi - lo)
                base = i / (n - 1) * 100
                nxt = (i + 1) / (n - 1) * 100
                percent = base + seg * (nxt - base)
                break
    return checkpoints, round(percent, 1)


def get_card_id():
    """A stable, unique card ID — generated once and stored, never
    regenerated on every request."""
    existing = get_meta('developer_card_id')
    if existing:
        return existing
    import secrets
    new_id = 'DEV-' + secrets.token_hex(3).upper()
    set_meta('developer_card_id', new_id)
    return new_id

def _title_for_level(level):
    for lo, hi, name in TITLES:
        if lo <= level <= hi:
            return name
    return 'Legend'


# card visual tiers — a separate scale from titles above, matching the
# Developer ID card's visual evolution (fewer, broader bands)
TIERS = [
    (1, 4, 1, 'Explorer'),
    (5, 9, 2, 'Builder'),
    (10, 19, 3, 'Developer'),
    (20, 29, 4, 'Full Stack'),
    (30, 39, 5, 'Elite'),
    (40, 9999, 6, 'Legend'),
]


def _tier_for_level(level):
    for lo, hi, num, name in TIERS:
        if lo <= level <= hi:
            return num, name
    return 6, 'Legend'


def get_card_id():
    """A stable, unique-looking Developer Card ID, deterministic (never
    random) so it never changes between requests or restarts."""
    import hashlib
    h = hashlib.sha256(b'buildwithayushmansingh-ayushman-singh').hexdigest().upper()
    return f'DEV-{h[:6]}'

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS xp_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT NOT NULL,
            activity_type TEXT NOT NULL,
            description TEXT NOT NULL,
            xp INTEGER NOT NULL,
            repository TEXT,
            project_id TEXT,
            external_event_id TEXT UNIQUE,
            timestamp TEXT NOT NULL
        )
    ''')
    # small key-value store — used to remember when GitHub was last polled,
    # so we don't hit its API on every single page view
    conn.execute('''
        CREATE TABLE IF NOT EXISTS github_sync_meta (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')
    conn.commit()
    conn.close()


def get_meta(key):
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute('SELECT value FROM github_sync_meta WHERE key = ?', (key,)).fetchone()
    conn.close()
    return row[0] if row else None


def set_meta(key, value):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        'INSERT INTO github_sync_meta (key, value) VALUES (?, ?) '
        'ON CONFLICT(key) DO UPDATE SET value = excluded.value',
        (key, value)
    )
    conn.commit()
    conn.close()


def count_today(activity_type):
    """How many transactions of this type were already recorded today —
    used for daily XP caps (e.g. capping how many pushes count per day)."""
    today = datetime.utcnow().date().isoformat()
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute(
        'SELECT COUNT(*) FROM xp_transactions WHERE activity_type = ? AND timestamp LIKE ?',
        (activity_type, today + '%')
    ).fetchone()
    conn.close()
    return row[0]

def award_xp(source, activity_type, description, xp, external_event_id=None,
             repository=None, project_id=None):
    """Insert one XP transaction. Returns False (no-op) if external_event_id
    was already recorded — this is the anti-duplicate guard the spec asks for."""
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute(
            '''INSERT INTO xp_transactions
               (source, activity_type, description, xp, repository, project_id,
                external_event_id, timestamp)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
            (source, activity_type, description, xp, repository, project_id,
             external_event_id, datetime.utcnow().isoformat())
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False  # this external_event_id already earned XP once
    finally:
        conn.close()


def get_total_xp():
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute('SELECT COALESCE(SUM(xp), 0) FROM xp_transactions').fetchone()
    conn.close()
    return row[0]


def get_transactions(limit=50):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        'SELECT * FROM xp_transactions ORDER BY timestamp DESC LIMIT ?', (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_progress():
    """The one function the templates use. Level/title/progress are always
    derived live from stored XP — there is no separate 'level' field to
    fall out of sync."""
    total_xp = get_total_xp()

    level = 0
    xp_floor = 0
    while True:
        needed = _xp_for_level(level + 1)
        if xp_floor + needed > total_xp:
            break
        xp_floor += needed
        level += 1

    level = max(level, 1)
    xp_into_level = total_xp - xp_floor
    xp_for_next = _xp_for_level(level + 1)
    progress_percent = min(round((xp_into_level / xp_for_next) * 100), 100) if xp_for_next else 100

    tier_num, tier_name = _tier_for_level(level)

    checkpoints, journey_percent = _journey_data(level)

    return {
        'total_xp': total_xp,
        'level': level,
        'title': _title_for_level(level),
        'tier': _tier_for_level(level),
        'card_id': get_card_id(),
        'xp_into_level': xp_into_level,
        'xp_for_next': xp_for_next,
        'xp_to_next': max(xp_for_next - xp_into_level, 0),
        'progress_percent': progress_percent,
        'journey_percent': journey_percent,
        'journey_checkpoints': checkpoints,
    }

def seed_initial_xp():
    """Awards XP for real, already-existing portfolio content — the 4 real
    projects and 4 real certificates already shown elsewhere on the site.
    Safe to call on every app start: each event has a fixed ID, so it can
    only ever be counted once."""
    real_projects = [
        ('wattwise', 'WattWise'),
        ('private-photo-vault', 'Private Photo Vault'),
        ('genai-project', 'GenAI Project'),
        ('personal-portfolio', 'Personal Portfolio'),
    ]
    for slug, name in real_projects:
        award_xp(
            source='portfolio', activity_type='project_created',
            description=f'Project created: {name}', xp=PROJECT_CREATED_XP,
            project_id=slug, external_event_id=f'seed_project_created_{slug}'
        )

    real_certificates = [
        'gold-eda', 'course-completion-eda', 'google-genai', 'nexus-quiz-ignite'
    ]
    for slug in real_certificates:
        award_xp(
            source='portfolio', activity_type='certificate_added',
            description=f'Certificate added: {slug}', xp=CERTIFICATE_ADDED_XP,
            external_event_id=f'seed_certificate_{slug}'
        )
        # ---- Activity / XP History (Phase 5) ----

ACTIVITY_DISPLAY = {
    'project_created': ('🚀', 'Project Created'),
    'certificate_added': ('🏆', 'Certificate Added'),
    'github_push': ('🐙', 'GitHub Commit'),
    'github_pr_opened': ('🔀', 'Pull Request'),
    'github_issue_opened': ('🐞', 'Issue Opened'),
    'github_issue_closed': ('✅', 'Issue Closed'),
    'github_repo_created': ('📦', 'Repository Created'),
    'achievement_unlocked': ('🏅', 'Achievement Unlocked'),
}


def _display_info(activity_type):
    return ACTIVITY_DISPLAY.get(activity_type, ('⚡', activity_type.replace('_', ' ').title()))


def categorize(activity_type, source):
    """Which filter bucket a transaction belongs to."""
    if source == 'achievement':
        return 'achievements'
    if source == 'github':
        return 'github'
    if activity_type == 'project_created':
        return 'projects'
    if activity_type == 'certificate_added':
        return 'certificates'
    return 'bonuses'


def _format_relative(timestamp_iso):
    try:
        dt = datetime.fromisoformat(timestamp_iso)
    except ValueError:
        return timestamp_iso
    now = datetime.utcnow()
    delta_days = (now.date() - dt.date()).days
    time_str = dt.strftime('%I:%M %p').lstrip('0')
    if delta_days <= 0:
        return f'Today, {time_str}'
    if delta_days == 1:
        return f'Yesterday, {time_str}'
    if delta_days < 7:
        return f'{delta_days} days ago'
    return dt.strftime('%b %d, %Y')


def get_xp_totals():
    now = datetime.utcnow()
    week_cutoff = (now - timedelta(days=7)).isoformat()
    month_cutoff = (now - timedelta(days=30)).isoformat()
    year_cutoff = (now - timedelta(days=365)).isoformat()

    conn = sqlite3.connect(DB_PATH)

    def sum_since(cutoff):
        row = conn.execute(
            'SELECT COALESCE(SUM(xp),0) FROM xp_transactions WHERE timestamp >= ?', (cutoff,)
        ).fetchone()
        return row[0]

    totals = {
        'total': get_total_xp(),
        'week': sum_since(week_cutoff),
        'month': sum_since(month_cutoff),
        'year': sum_since(year_cutoff),
    }
    conn.close()
    return totals


def get_activity_feed(category='all', date_range='all', limit=300):
    """Real, filtered transaction history — every entry is a stored row,
    never a fake/backfilled estimate."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        'SELECT * FROM xp_transactions ORDER BY timestamp DESC LIMIT ?', (limit,)
    ).fetchall()
    conn.close()
    txns = [dict(r) for r in rows]

    if category != 'all':
        txns = [t for t in txns if categorize(t['activity_type'], t['source']) == category]

    if date_range != 'all':
        now = datetime.utcnow()
        if date_range == 'today':
            cutoff = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif date_range == 'week':
            cutoff = now - timedelta(days=7)
        elif date_range == 'month':
            cutoff = now - timedelta(days=30)
        else:
            cutoff = None
        if cutoff:
            cutoff_str = cutoff.isoformat()
            txns = [t for t in txns if t['timestamp'] >= cutoff_str]

    feed = []
    for t in txns:
        icon, label = _display_info(t['activity_type'])
        feed.append({
            **t,
            'icon': icon,
            'label': label,
            'relative_time': _format_relative(t['timestamp']),
        })
    return feed