"""
Admin panel for Mining Balance configuration.

Provides a web UI to view and edit mining balance parameters
and daily progression data. Protected by simple login/password.
"""

import secrets
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Form, HTTPException, Request, Response, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.mining_balance_service import mining_balance_service

router = APIRouter(prefix="/admin", tags=["Admin Panel"])

# ──────────────────────────────────────────────
# Simple session store (in-memory; restarts clear sessions)
# ──────────────────────────────────────────────

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "wattstap333"
SESSION_COOKIE = "admin_session"

_sessions: dict[str, datetime] = {}


def _create_session() -> str:
    token = secrets.token_urlsafe(32)
    _sessions[token] = datetime.utcnow()
    return token


def _validate_session(request: Request) -> bool:
    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        return False
    return token in _sessions


def _require_auth(request: Request):
    if not _validate_session(request):
        raise HTTPException(status_code=status.HTTP_307_TEMPORARY_REDIRECT,
                            headers={"Location": "/admin/login"})


# ──────────────────────────────────────────────
# Login / Logout
# ──────────────────────────────────────────────

@router.get("/login", response_class=HTMLResponse, include_in_schema=False)
async def login_page(request: Request, error: str = ""):
    return HTMLResponse(_render_login(error))


@router.post("/login", response_class=HTMLResponse, include_in_schema=False)
async def login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
):
    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        token = _create_session()
        resp = RedirectResponse("/admin/", status_code=status.HTTP_302_FOUND)
        resp.set_cookie(SESSION_COOKIE, token, httponly=True, samesite="lax", max_age=86400)
        return resp
    return HTMLResponse(_render_login("Invalid username or password"))


@router.get("/logout", include_in_schema=False)
async def logout(request: Request):
    token = request.cookies.get(SESSION_COOKIE)
    if token and token in _sessions:
        del _sessions[token]
    resp = RedirectResponse("/admin/login", status_code=status.HTTP_302_FOUND)
    resp.delete_cookie(SESSION_COOKIE)
    return resp


# ──────────────────────────────────────────────
# Dashboard
# ──────────────────────────────────────────────

@router.get("/", response_class=HTMLResponse, include_in_schema=False)
async def dashboard(request: Request, db: AsyncSession = Depends(get_db)):
    if not _validate_session(request):
        return RedirectResponse("/admin/login", status_code=status.HTTP_302_FOUND)

    params = await mining_balance_service.get_active_balance(db)
    return HTMLResponse(_render_dashboard(params))


# ──────────────────────────────────────────────
# API: Update start parameters
# ──────────────────────────────────────────────

@router.post("/update-params", response_class=HTMLResponse, include_in_schema=False)
async def update_params(request: Request, db: AsyncSession = Depends(get_db)):
    if not _validate_session(request):
        return RedirectResponse("/admin/login", status_code=status.HTTP_302_FOUND)

    form = await request.form()
    params = await mining_balance_service.get_active_balance(db)
    if not params:
        return RedirectResponse("/admin/?error=not_found", status_code=status.HTTP_302_FOUND)

    int_fields = {
        "coins_per_tap", "exp_per_tap", "energy_cost_per_tap",
        "start_capacity_hits", "avg_playtime_minutes", "taps_per_second",
        "profit_per_hour", "max_hours_offline", "sessions_per_day",
    }
    float_fields = {
        "cooldown_per_hit_sec", "crit_multiplier", "chance_crit_percent",
    }

    for field in int_fields:
        val = form.get(field)
        if val is not None and val != "":
            try:
                setattr(params, field, int(val))
            except ValueError:
                pass

    for field in float_fields:
        val = form.get(field)
        if val is not None and val != "":
            try:
                setattr(params, field, float(val))
            except ValueError:
                pass

    params.updated_at = datetime.utcnow()
    await db.flush()
    return RedirectResponse("/admin/?success=params", status_code=status.HTTP_302_FOUND)


# ──────────────────────────────────────────────
# API: Update daily progression
# ──────────────────────────────────────────────

@router.post("/update-progression", response_class=HTMLResponse, include_in_schema=False)
async def update_progression(request: Request, db: AsyncSession = Depends(get_db)):
    if not _validate_session(request):
        return RedirectResponse("/admin/login", status_code=status.HTTP_302_FOUND)

    form = await request.form()
    params = await mining_balance_service.get_active_balance(db)
    if not params:
        return RedirectResponse("/admin/?error=not_found", status_code=status.HTTP_302_FOUND)

    daily = sorted(params.daily_progression, key=lambda d: d.day)

    for day_row in daily:
        day = day_row.day
        int_cols = ["playtime_sec", "taps_per_session", "taps_per_day", "exp_per_day", "cumulative_exp"]
        float_cols = ["coins_from_taps", "coins_from_offline_bonus", "profit_coins", "cumulative_profit_coins"]

        for col in int_cols:
            key = f"day_{day}_{col}"
            val = form.get(key)
            if val is not None and val != "":
                try:
                    setattr(day_row, col, int(float(val)))
                except ValueError:
                    pass

        for col in float_cols:
            key = f"day_{day}_{col}"
            val = form.get(key)
            if val is not None and val != "":
                try:
                    setattr(day_row, col, float(val))
                except ValueError:
                    pass

    params.updated_at = datetime.utcnow()
    await db.flush()
    return RedirectResponse("/admin/?success=progression", status_code=status.HTTP_302_FOUND)


# ──────────────────────────────────────────────
# API: Re-seed from CSV
# ──────────────────────────────────────────────

@router.post("/reseed", response_class=HTMLResponse, include_in_schema=False)
async def reseed(request: Request, db: AsyncSession = Depends(get_db)):
    if not _validate_session(request):
        return RedirectResponse("/admin/login", status_code=status.HTTP_302_FOUND)

    from app.routers.mining_balance import _get_csv_path
    csv_path = _get_csv_path()
    success, message, days = await mining_balance_service.seed_from_csv_file(
        db, csv_path, version="default", force=True
    )
    if success:
        return RedirectResponse("/admin/?success=reseed", status_code=status.HTTP_302_FOUND)
    return RedirectResponse(f"/admin/?error=reseed", status_code=status.HTTP_302_FOUND)


# ══════════════════════════════════════════════
# HTML Templates (self-contained, no Jinja dependency required)
# ══════════════════════════════════════════════

_CSS = """
:root {
    --bg: #0f1117;
    --surface: #1a1d27;
    --surface2: #242734;
    --border: #2e3144;
    --accent: #6c5ce7;
    --accent-hover: #7c6df7;
    --accent-light: rgba(108,92,231,0.15);
    --text: #e8e8f0;
    --text-muted: #8b8da3;
    --success: #00b894;
    --danger: #ff6b6b;
    --warning: #fdcb6e;
    --radius: 12px;
    --radius-sm: 8px;
}
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, sans-serif;
    background: var(--bg);
    color: var(--text);
    min-height: 100vh;
    line-height: 1.6;
}
a { color: var(--accent); text-decoration: none; }
a:hover { text-decoration: underline; }

/* Header */
.header {
    background: var(--surface);
    border-bottom: 1px solid var(--border);
    padding: 16px 32px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    position: sticky;
    top: 0;
    z-index: 100;
    backdrop-filter: blur(10px);
}
.header h1 { font-size: 20px; font-weight: 600; }
.header h1 span { color: var(--accent); }
.header-actions { display: flex; gap: 12px; align-items: center; }
.header-actions .version-badge {
    background: var(--accent-light);
    color: var(--accent);
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 13px;
    font-weight: 500;
}

/* Container */
.container { max-width: 1400px; margin: 0 auto; padding: 24px 32px; }

/* Alert */
.alert {
    padding: 14px 20px;
    border-radius: var(--radius-sm);
    margin-bottom: 20px;
    font-size: 14px;
    font-weight: 500;
    display: flex;
    align-items: center;
    gap: 10px;
}
.alert-success { background: rgba(0,184,148,0.12); color: var(--success); border: 1px solid rgba(0,184,148,0.3); }
.alert-error { background: rgba(255,107,107,0.12); color: var(--danger); border: 1px solid rgba(255,107,107,0.3); }

/* Cards */
.card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    margin-bottom: 24px;
    overflow: hidden;
}
.card-header {
    padding: 18px 24px;
    border-bottom: 1px solid var(--border);
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.card-header h2 { font-size: 16px; font-weight: 600; }
.card-body { padding: 24px; }

/* Metadata row */
.meta-row {
    display: flex;
    gap: 32px;
    margin-bottom: 16px;
    flex-wrap: wrap;
}
.meta-item { font-size: 13px; color: var(--text-muted); }
.meta-item strong { color: var(--text); margin-left: 6px; }

/* Form grid */
.form-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 16px;
}
.form-group { display: flex; flex-direction: column; gap: 6px; }
.form-group label {
    font-size: 12px;
    font-weight: 600;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.5px;
}
.form-group input {
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    padding: 10px 14px;
    color: var(--text);
    font-size: 14px;
    font-family: 'SF Mono', 'Consolas', 'Monaco', monospace;
    transition: border-color 0.2s, box-shadow 0.2s;
}
.form-group input:focus {
    outline: none;
    border-color: var(--accent);
    box-shadow: 0 0 0 3px var(--accent-light);
}
.form-group input:hover { border-color: #444; }

/* Buttons */
.btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    padding: 10px 20px;
    border: none;
    border-radius: var(--radius-sm);
    font-size: 14px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s;
}
.btn-primary { background: var(--accent); color: white; }
.btn-primary:hover { background: var(--accent-hover); transform: translateY(-1px); box-shadow: 0 4px 12px rgba(108,92,231,0.4); }
.btn-danger { background: var(--danger); color: white; }
.btn-danger:hover { background: #ff5252; transform: translateY(-1px); }
.btn-outline {
    background: transparent;
    border: 1px solid var(--border);
    color: var(--text-muted);
}
.btn-outline:hover { border-color: var(--accent); color: var(--accent); }
.btn-sm { padding: 6px 14px; font-size: 13px; }

.actions-row { display: flex; gap: 12px; margin-top: 20px; flex-wrap: wrap; align-items: center; }

/* Table */
.table-wrapper { overflow-x: auto; }
table {
    width: 100%;
    border-collapse: collapse;
    font-size: 13px;
}
thead th {
    background: var(--surface2);
    padding: 10px 12px;
    text-align: right;
    font-weight: 600;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    color: var(--text-muted);
    white-space: nowrap;
    position: sticky;
    top: 0;
}
thead th:first-child { text-align: center; }
tbody td { padding: 6px 8px; border-bottom: 1px solid var(--border); }
tbody tr:hover { background: var(--surface2); }
tbody td input {
    background: var(--bg);
    border: 1px solid transparent;
    border-radius: 6px;
    padding: 6px 10px;
    color: var(--text);
    font-size: 13px;
    font-family: 'SF Mono', 'Consolas', 'Monaco', monospace;
    width: 100%;
    text-align: right;
    transition: border-color 0.2s;
}
tbody td input:focus {
    outline: none;
    border-color: var(--accent);
    box-shadow: 0 0 0 2px var(--accent-light);
}
tbody td input:hover { border-color: #444; }
.day-cell {
    text-align: center !important;
    font-weight: 700;
    color: var(--accent);
    min-width: 40px;
}

/* Login page */
.login-wrapper {
    display: flex;
    min-height: 100vh;
    align-items: center;
    justify-content: center;
}
.login-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 40px;
    width: 380px;
    text-align: center;
}
.login-card h1 { margin-bottom: 8px; font-size: 24px; }
.login-card p { color: var(--text-muted); margin-bottom: 28px; font-size: 14px; }
.login-card .form-group { margin-bottom: 16px; text-align: left; }
.login-card .form-group input { width: 100%; }
.login-card .btn { width: 100%; padding: 12px; margin-top: 8px; }

/* Responsive */
@media (max-width: 768px) {
    .header { padding: 12px 16px; }
    .container { padding: 16px; }
    .form-grid { grid-template-columns: 1fr 1fr; }
    .meta-row { gap: 16px; }
}
"""


def _render_login(error: str = "") -> str:
    error_html = ""
    if error:
        error_html = f'<div class="alert alert-error">{_esc(error)}</div>'

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>WattsTap Admin — Login</title>
    <style>{_CSS}</style>
</head>
<body>
<div class="login-wrapper">
    <div class="login-card">
        <h1>WattsTap <span style="color:var(--accent)">Admin</span></h1>
        <p>Mining Balance Configuration</p>
        {error_html}
        <form method="post" action="/admin/login">
            <div class="form-group">
                <label>Username</label>
                <input type="text" name="username" placeholder="admin" autocomplete="username" required autofocus>
            </div>
            <div class="form-group">
                <label>Password</label>
                <input type="password" name="password" placeholder="••••••••" autocomplete="current-password" required>
            </div>
            <button type="submit" class="btn btn-primary">Sign In</button>
        </form>
    </div>
</div>
</body>
</html>"""


def _render_dashboard(params) -> str:
    if not params:
        return _render_empty_state()

    daily = sorted(params.daily_progression, key=lambda d: d.day) if params.daily_progression else []

    success_msg = ""

    # Build start parameters form
    param_fields = [
        ("coins_per_tap", "Coins Per Tap", "int"),
        ("exp_per_tap", "Exp Per Tap", "int"),
        ("energy_cost_per_tap", "Energy Cost Per Tap", "int"),
        ("start_capacity_hits", "Start Capacity Hits", "int"),
        ("cooldown_per_hit_sec", "Cooldown Per Hit (sec)", "float"),
        ("crit_multiplier", "Crit Multiplier", "float"),
        ("chance_crit_percent", "Chance Crit %", "float"),
        ("avg_playtime_minutes", "Avg Playtime (min)", "int"),
        ("taps_per_second", "Taps Per Second", "int"),
        ("profit_per_hour", "Profit Per Hour", "int"),
        ("max_hours_offline", "Max Hours Offline", "int"),
        ("sessions_per_day", "Sessions Per Day", "int"),
    ]

    params_html = ""
    for field, label, ftype in param_fields:
        val = getattr(params, field, "")
        step = "0.01" if ftype == "float" else "1"
        input_type = "number"
        params_html += f"""
        <div class="form-group">
            <label>{_esc(label)}</label>
            <input type="{input_type}" name="{field}" value="{val}" step="{step}">
        </div>"""

    # Build daily progression table
    prog_columns = [
        ("playtime_sec", "Playtime (sec)", "int"),
        ("taps_per_session", "Taps/Session", "int"),
        ("taps_per_day", "Taps/Day", "int"),
        ("exp_per_day", "Exp/Day", "int"),
        ("coins_from_taps", "Coins Taps", "float"),
        ("coins_from_offline_bonus", "Coins Offline", "float"),
        ("profit_coins", "Profit Coins", "float"),
        ("cumulative_profit_coins", "Cum. Profit", "float"),
        ("cumulative_exp", "Cum. Exp", "int"),
    ]

    thead = "<th>Day</th>"
    for col, label, _ in prog_columns:
        thead += f"<th>{_esc(label)}</th>"

    tbody = ""
    for day_row in daily:
        day = day_row.day
        tbody += f'<tr><td class="day-cell">{day}</td>'
        for col, _, ftype in prog_columns:
            val = getattr(day_row, col, "")
            step = "0.01" if ftype == "float" else "1"
            name = f"day_{day}_{col}"
            tbody += f'<td><input type="number" name="{name}" value="{val}" step="{step}"></td>'
        tbody += "</tr>"

    created = params.created_at.strftime("%Y-%m-%d %H:%M") if params.created_at else "—"
    updated = params.updated_at.strftime("%Y-%m-%d %H:%M") if params.updated_at else "—"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>WattsTap Admin — Mining Balance</title>
    <style>{_CSS}</style>
</head>
<body>
<div class="header">
    <h1>WattsTap <span>Admin</span></h1>
    <div class="header-actions">
        <span class="version-badge">v {_esc(params.version)}</span>
        <a href="/admin/logout" class="btn btn-outline btn-sm">Logout</a>
    </div>
</div>
<div class="container">

    <div id="alert-area"></div>

    <!-- Metadata -->
    <div class="meta-row">
        <div class="meta-item">Status: <strong style="color:var(--success)">{'Active' if params.is_active else 'Inactive'}</strong></div>
        <div class="meta-item">Created: <strong>{created}</strong></div>
        <div class="meta-item">Updated: <strong>{updated}</strong></div>
        <div class="meta-item">Days: <strong>{len(daily)}</strong></div>
    </div>

    <!-- Start Parameters -->
    <form method="post" action="/admin/update-params" id="params-form">
    <div class="card">
        <div class="card-header">
            <h2>Start Parameters</h2>
        </div>
        <div class="card-body">
            <div class="form-grid">
                {params_html}
            </div>
            <div class="actions-row">
                <button type="submit" class="btn btn-primary">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/><polyline points="17 21 17 13 7 13 7 21"/><polyline points="7 3 7 8 15 8"/></svg>
                    Save Parameters
                </button>
            </div>
        </div>
    </div>
    </form>

    <!-- Daily Progression -->
    <form method="post" action="/admin/update-progression" id="prog-form">
    <div class="card">
        <div class="card-header">
            <h2>Daily Progression (30 days)</h2>
        </div>
        <div class="card-body">
            <div class="table-wrapper">
            <table>
                <thead><tr>{thead}</tr></thead>
                <tbody>{tbody}</tbody>
            </table>
            </div>
            <div class="actions-row">
                <button type="submit" class="btn btn-primary">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/><polyline points="17 21 17 13 7 13 7 21"/><polyline points="7 3 7 8 15 8"/></svg>
                    Save Progression
                </button>
            </div>
        </div>
    </div>
    </form>

    <!-- Danger zone -->
    <div class="card" style="border-color: rgba(255,107,107,0.3);">
        <div class="card-header">
            <h2 style="color:var(--danger)">Danger Zone</h2>
        </div>
        <div class="card-body">
            <p style="color:var(--text-muted); margin-bottom:16px; font-size:14px;">
                Re-seed from CSV will <strong>overwrite</strong> all current parameters and progression data with the original CSV file.
            </p>
            <form method="post" action="/admin/reseed" onsubmit="return confirm('Are you sure? This will overwrite all current data with the CSV file.')">
                <button type="submit" class="btn btn-danger">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="1 4 1 10 7 10"/><polyline points="23 20 23 14 17 14"/><path d="M20.49 9A9 9 0 0 0 5.64 5.64L1 10m22 4l-4.64 4.36A9 9 0 0 1 3.51 15"/></svg>
                    Re-seed from CSV
                </button>
            </form>
        </div>
    </div>

</div>

<script>
// Show alerts from URL params
const params = new URLSearchParams(window.location.search);
const area = document.getElementById('alert-area');
if (params.get('success')) {{
    const msgs = {{ params: 'Start parameters saved successfully!', progression: 'Daily progression saved successfully!', reseed: 'Data re-seeded from CSV successfully!' }};
    const msg = msgs[params.get('success')] || 'Operation completed successfully!';
    area.innerHTML = '<div class="alert alert-success">' + msg + '</div>';
    history.replaceState(null, '', '/admin/');
}}
if (params.get('error')) {{
    const msgs = {{ not_found: 'Mining balance config not found.', reseed: 'Failed to re-seed from CSV.' }};
    const msg = msgs[params.get('error')] || 'An error occurred.';
    area.innerHTML = '<div class="alert alert-error">' + msg + '</div>';
    history.replaceState(null, '', '/admin/');
}}

// Auto-hide alerts after 5s
setTimeout(() => {{
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(a => {{ a.style.transition = 'opacity 0.3s'; a.style.opacity = '0'; setTimeout(() => a.remove(), 300); }});
}}, 5000);
</script>
</body>
</html>"""


def _render_empty_state() -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>WattsTap Admin — No Data</title>
    <style>{_CSS}</style>
</head>
<body>
<div class="header">
    <h1>WattsTap <span>Admin</span></h1>
    <div class="header-actions">
        <a href="/admin/logout" class="btn btn-outline btn-sm">Logout</a>
    </div>
</div>
<div class="container">
    <div class="card">
        <div class="card-body" style="text-align:center; padding:60px;">
            <h2 style="margin-bottom:12px;">No Mining Balance Data</h2>
            <p style="color:var(--text-muted); margin-bottom:24px;">
                The database has no mining balance configuration yet. Seed it from the CSV file to get started.
            </p>
            <form method="post" action="/admin/reseed">
                <button type="submit" class="btn btn-primary">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="1 4 1 10 7 10"/><polyline points="23 20 23 14 17 14"/><path d="M20.49 9A9 9 0 0 0 5.64 5.64L1 10m22 4l-4.64 4.36A9 9 0 0 1 3.51 15"/></svg>
                    Seed from CSV
                </button>
            </form>
        </div>
    </div>
</div>
</body>
</html>"""


def _esc(s) -> str:
    """Escape HTML special characters."""
    if s is None:
        return ""
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
