from __future__ import annotations

import os
import sys
import csv
import math
import subprocess
from pathlib import Path
from typing import List, Dict, Optional

from fastapi import FastAPI, Request, Form, BackgroundTasks, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# Use project root as base
BASE_DIR = Path(__file__).resolve().parents[1]
AGENT_PATH = str(BASE_DIR / "agent.py")
LEADS_CSV = os.getenv("LEADS_CSV_PATH", str(BASE_DIR / "leads.csv"))

# Import campaign mapping and display helper from backend
try:
    sys.path.insert(0, str(BASE_DIR))
    from agent import CAMPAIGNS, _campaign_display_name
except Exception:
    CAMPAIGNS = {
        "Default": ("prompts", "ENHANCED_DEMANDIFY_CALLER_INSTRUCTIONS", "SESSION_INSTRUCTION"),
        "SplashBI": ("prompts2", "ENHANCED_DEMANDIFY_CALLER_INSTRUCTIONS", "SESSION_INSTRUCTION"),
        "KonfHub": ("prompts3", "ENHANCED_DEMANDIFY_CALLER_INSTRUCTIONS", "SESSION_INSTRUCTION"),
        "Zoom Phone": ("prompts4", "ENHANCED_DEMANDIFY_CALLER_INSTRUCTIONS", "SESSION_INSTRUCTION"),
    }
    def _campaign_display_name(name: str) -> str:  # type: ignore
        return name

app = FastAPI(title="AI Calling Agent - Web UI")

# Mount static and templates
STATIC_DIR = Path(__file__).resolve().parent / "static"
TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"
STATIC_DIR.mkdir(parents=True, exist_ok=True)
TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

PAGE_SIZE = 8

# LiveKit credentials (for token issuance)
LIVEKIT_URL = os.getenv("LIVEKIT_URL", "")
LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY", "")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET", "")

# We'll sign tokens using PyJWT to avoid extra deps
import time
import jwt  # PyJWT
import httpx

# Cache for vendor script to avoid repeated external fetches
_LK_JS_CACHE: dict[str, bytes] = {}

# Global state for managing a single running console call
from threading import Lock, Thread
import signal

_proc_lock = Lock()
CURRENT_PROC: Optional[subprocess.Popen] = None
CURRENT_STATUS: str = "idle"  # idle | running | stopping
CURRENT_LEAD_INDEX: Optional[int] = None  # 1-based
SELECTED_CAMPAIGN: Optional[str] = None
AUTO_NEXT: bool = False
_WATCHER_STARTED: bool = False


def read_leads(csv_path: str) -> List[Dict[str, str]]:
    """Read leads with as many useful fields as available."""
    leads: List[Dict[str, str]] = []
    try:
        with open(csv_path, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                leads.append({
                    "prospect_name": (row.get("prospect_name") or "").strip(),
                    "company_name": (row.get("company_name") or "").strip(),
                    "job_title": (row.get("job_title") or "").strip(),
                    "phone": (row.get("phone") or "").strip(),
                    "email": (row.get("email") or "").strip(),
                    "timezone": (row.get("timezone") or "").strip(),
                })
    except FileNotFoundError:
        pass
    return leads


def get_lead_by_index_1based(idx1: int) -> Optional[Dict[str, str]]:
    try:
        leads = read_leads(LEADS_CSV)
        if 1 <= idx1 <= len(leads):
            return leads[idx1 - 1]
    except Exception:
        pass
    return None


def spawn_call(lead_index_1based: int, campaign_key: Optional[str]) -> None:
    env = os.environ.copy()
    env["RUN_SINGLE_CALL"] = "1"
    env["LEAD_INDEX"] = str(lead_index_1based)

    # Apply campaign env if provided
    if campaign_key and campaign_key in CAMPAIGNS:
        mod, agent_attr, session_attr = CAMPAIGNS[campaign_key]
        env["CAMPAIGN_PROMPT_MODULE"] = mod
        env["CAMPAIGN_AGENT_NAME"] = agent_attr
        env["CAMPAIGN_SESSION_NAME"] = session_attr

    # Launch console subcommand to get audio I/O and track process
    global CURRENT_PROC, CURRENT_STATUS, CURRENT_LEAD_INDEX
    with _proc_lock:
        # If a process is already running, do not start another
        if CURRENT_PROC and CURRENT_PROC.poll() is None:
            return
        creationflags = 0
        if sys.platform == "win32":
            # Create new process group to allow signal/termination management
            creationflags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
        CURRENT_PROC = subprocess.Popen(
            [sys.executable, AGENT_PATH, "console"], env=env, creationflags=creationflags
        )
        CURRENT_STATUS = "running"
        CURRENT_LEAD_INDEX = lead_index_1based


def spawn_agent_connect_room(room_name: str, campaign_key: Optional[str]) -> None:
    """Spawn agent to connect to a specific room so the browser can converse with it."""
    env = os.environ.copy()
    env["RUN_SINGLE_CALL"] = "1"
    if campaign_key and campaign_key in CAMPAIGNS:
        mod, agent_attr, session_attr = CAMPAIGNS[campaign_key]
        env["CAMPAIGN_PROMPT_MODULE"] = mod
        env["CAMPAIGN_AGENT_NAME"] = agent_attr
        env["CAMPAIGN_SESSION_NAME"] = session_attr
    # Use LiveKit CLI subcommand 'connect' with a room name; the Agents CLI will join that room
    subprocess.Popen([sys.executable, AGENT_PATH, "connect", "--room", room_name], env=env)


def _end_current_call() -> bool:
    """Attempt to gracefully stop the current console call. Returns True if a process was signaled/terminated."""
    global CURRENT_PROC, CURRENT_STATUS
    with _proc_lock:
        proc = CURRENT_PROC
        if not proc or proc.poll() is not None:
            CURRENT_PROC = None
            CURRENT_STATUS = "idle"
            return False
        CURRENT_STATUS = "stopping"
        try:
            if sys.platform == "win32":
                # Best-effort terminate on Windows
                proc.terminate()
            else:
                proc.send_signal(signal.SIGINT)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass
        return True


def _cleanup_if_exited() -> None:
    """Reset globals if the process has exited."""
    global CURRENT_PROC, CURRENT_STATUS
    with _proc_lock:
        if CURRENT_PROC and CURRENT_PROC.poll() is not None:
            CURRENT_PROC = None
            CURRENT_STATUS = "idle"


def _watcher_loop():
    """Background loop to auto-start next call when a call ends and AUTO_NEXT is enabled."""
    last_running = False
    while True:
        try:
            with _proc_lock:
                running = CURRENT_PROC is not None and CURRENT_PROC.poll() is None
                lead_idx = CURRENT_LEAD_INDEX
                campaign = SELECTED_CAMPAIGN
            # Transition: running -> not running
            if last_running and not running:
                # Ensure cleanup
                _cleanup_if_exited()
                if AUTO_NEXT and lead_idx is not None:
                    # Start next automatically
                    try:
                        spawn_call(lead_idx + 1, campaign)
                    except Exception:
                        pass
            last_running = running
        except Exception:
            pass
        time.sleep(1)


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, page: int = 1, campaign: Optional[str] = None):
    leads = read_leads(LEADS_CSV)
    total = len(leads)
    total_pages = max(1, math.ceil(total / PAGE_SIZE))
    page = max(1, min(page, total_pages))
    start = (page - 1) * PAGE_SIZE
    end = min(start + PAGE_SIZE, total)

    # Clean campaign names for dropdown - exclude 'Default' variants to keep only three campaigns
    campaign_options = []
    for k in CAMPAIGNS.keys():
        clean = _campaign_display_name(k)
        if clean.lower().startswith("default"):
            continue
        campaign_options.append({"key": k, "label": clean, "selected": (campaign == k)})

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "campaign": campaign,
            "campaign_options": campaign_options,
            "leads": leads[start:end],
            "page": page,
            "total_pages": total_pages,
            "start_index": start,  # zero-based for row numbering
        },
    )


@app.post("/call")
async def call_lead(
    background_tasks: BackgroundTasks,
    lead_global_index: int = Form(...),  # zero-based from page
    campaign: Optional[str] = Form(None),
    page: int = Form(1),
):
    # Convert zero-based to one-based for backend
    lead_index_1based = lead_global_index + 1
    background_tasks.add_task(spawn_call, lead_index_1based, campaign)

    # Redirect back to the current page
    url = f"/?page={page}"
    if campaign:
        url += f"&campaign={campaign}"
    return RedirectResponse(url=url, status_code=303)


# -----------------------------
# JSON APIs for console control
# -----------------------------

@app.post("/api/select_campaign")
async def api_select_campaign(campaign: Optional[str] = Form(None)):
    global SELECTED_CAMPAIGN
    if campaign and campaign not in CAMPAIGNS:
        raise HTTPException(status_code=400, detail="Unknown campaign")
    SELECTED_CAMPAIGN = campaign
    label = _campaign_display_name(campaign) if campaign else None
    return JSONResponse({"ok": True, "campaign": campaign, "campaign_label": label})


@app.post("/api/start_call")
async def api_start_call(lead_global_index: int = Form(...), campaign: Optional[str] = Form(None)):
    # Prefer explicit campaign from form; otherwise use last selected
    effective_campaign = campaign if campaign is not None else SELECTED_CAMPAIGN
    idx1 = lead_global_index + 1
    spawn_call(idx1, effective_campaign)
    return JSONResponse({
        "ok": True,
        "status": CURRENT_STATUS,
        "lead_index": CURRENT_LEAD_INDEX,
        "campaign": effective_campaign,
        "campaign_label": _campaign_display_name(effective_campaign) if effective_campaign else None,
    })


@app.post("/api/end_call")
async def api_end_call(auto_next: bool = Form(True)):
    """End current call; optionally start the next call automatically."""
    global CURRENT_LEAD_INDEX
    prev = CURRENT_LEAD_INDEX
    had_proc = _end_current_call()
    # Wait briefly for process to exit
    time.sleep(0.4)
    _cleanup_if_exited()
    started_next = False
    if auto_next and prev is not None:
        next_idx = prev + 1
        spawn_call(next_idx, SELECTED_CAMPAIGN)
        started_next = True
    return JSONResponse({
        "ok": True,
        "had_proc": had_proc,
        "status": CURRENT_STATUS,
        "lead_index": CURRENT_LEAD_INDEX,
        "auto_next_started": started_next,
        "campaign": SELECTED_CAMPAIGN,
        "campaign_label": _campaign_display_name(SELECTED_CAMPAIGN) if SELECTED_CAMPAIGN else None,
    })


@app.get("/api/status")
async def api_status():
    _cleanup_if_exited()
    running = CURRENT_PROC is not None and CURRENT_PROC.poll() is None
    lead_details = get_lead_by_index_1based(CURRENT_LEAD_INDEX) if CURRENT_LEAD_INDEX else None
    return JSONResponse({
        "status": CURRENT_STATUS,
        "running": running,
        "lead_index": CURRENT_LEAD_INDEX,
        "campaign": SELECTED_CAMPAIGN,
        "campaign_label": _campaign_display_name(SELECTED_CAMPAIGN) if SELECTED_CAMPAIGN else None,
        "auto_next": AUTO_NEXT,
        "lead": lead_details or {},
    })


@app.post("/api/auto_next")
async def api_auto_next(enabled: bool = Form(...)):
    global AUTO_NEXT
    AUTO_NEXT = bool(str(enabled).lower() in ["1", "true", "yes", "on"])
    return JSONResponse({"ok": True, "auto_next": AUTO_NEXT})


@app.post("/api/stop_all")
async def api_stop_all():
    """Disable auto-next and end any running call (end whole session)."""
    global AUTO_NEXT
    AUTO_NEXT = False
    _end_current_call()
    time.sleep(0.4)
    _cleanup_if_exited()
    return JSONResponse({"ok": True, "status": CURRENT_STATUS, "auto_next": AUTO_NEXT})


# Start watcher thread once
def _ensure_watcher_started():
    global _WATCHER_STARTED
    if not _WATCHER_STARTED:
        t = Thread(target=_watcher_loop, daemon=True)
        t.start()
        _WATCHER_STARTED = True


_ensure_watcher_started()


@app.get("/vendor/livekit-client.js")
async def vendor_livekit_client():
    """Serve the LiveKit Web SDK via backend to bypass CDN/network blocks.
    Caches the file in memory for subsequent requests.
    """
    cache_key = "livekit-client-2.3.3"
    if cache_key in _LK_JS_CACHE:
        return Response(content=_LK_JS_CACHE[cache_key], media_type="application/javascript")
    cdns = [
        "https://cdn.livekit.io/npm/livekit-client/2.3.3/livekit-client.umd.min.js",
        "https://unpkg.com/livekit-client@2.3.3/dist/livekit-client.umd.min.js",
        "https://cdn.jsdelivr.net/npm/livekit-client@2.3.3/dist/livekit-client.umd.min.js",
    ]
    for url in cdns:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                r = await client.get(url)
                if r.status_code == 200 and r.content:
                    _LK_JS_CACHE[cache_key] = r.content
                    return Response(content=r.content, media_type="application/javascript")
        except Exception:
            continue
    raise HTTPException(status_code=502, detail="Failed to load LiveKit client script from CDNs")


@app.get("/vendor/livekit-client.esm.js")
async def vendor_livekit_client_esm():
    """Serve the LiveKit Web ESM build via backend to bypass CORS/CDN blocks."""
    cache_key = "livekit-client-esm-2.3.3"
    if cache_key in _LK_JS_CACHE:
        return Response(content=_LK_JS_CACHE[cache_key], media_type="application/javascript")
    cdns = [
        "https://unpkg.com/livekit-client@2.3.3/dist/livekit-client.esm.min.js",
        "https://cdn.jsdelivr.net/npm/livekit-client@2.3.3/dist/livekit-client.esm.min.js",
        "https://unpkg.com/livekit-client/dist/livekit-client.esm.min.js",
    ]
    for url in cdns:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                r = await client.get(url)
                if r.status_code == 200 and r.content:
                    _LK_JS_CACHE[cache_key] = r.content
                    return Response(content=r.content, media_type="application/javascript")
        except Exception:
            continue
    raise HTTPException(status_code=502, detail="Failed to load LiveKit ESM module from CDNs")


@app.post("/browser/start")
async def start_browser_call(
    background_tasks: BackgroundTasks,
    lead_global_index: int = Form(...),
    campaign: Optional[str] = Form(None),
):
    # Create a simple deterministic room name by index (you may swap for UUID)
    room_name = f"room-{lead_global_index+1}"
    background_tasks.add_task(spawn_agent_connect_room, room_name, campaign)
    return RedirectResponse(url=f"/browser/call?room={room_name}{'&campaign='+campaign if campaign else ''}", status_code=303)


@app.get("/browser/call", response_class=HTMLResponse)
async def browser_call(request: Request, room: str, campaign: Optional[str] = None):
    if not LIVEKIT_URL:
        raise HTTPException(status_code=500, detail="LIVEKIT_URL not configured")
    return templates.TemplateResponse(
        "browser_call.html",
        {
            "request": request,
            "room": room,
            "livekit_url": LIVEKIT_URL,
            "campaign": campaign or "",
        },
    )


@app.get("/api/token")
async def issue_token(room: str, identity: str):
    if not (LIVEKIT_API_KEY and LIVEKIT_API_SECRET and LIVEKIT_URL):
        raise HTTPException(status_code=500, detail="LiveKit credentials not configured")
    now = int(time.time())
    payload = {
        "iss": LIVEKIT_API_KEY,
        "sub": LIVEKIT_API_KEY,
        "nbf": now - 10,
        "exp": now + 60 * 10,  # 10 minutes
        "video": {
            "room": room,
            "roomJoin": True,
            "canPublish": True,
            "canSubscribe": True,
        },
        "identity": identity,
        "name": identity,
    }
    token = jwt.encode(payload, LIVEKIT_API_SECRET, algorithm="HS256")
    return JSONResponse({"token": token})


@app.post("/next")
async def call_next(
    background_tasks: BackgroundTasks,
    next_index: int = Form(...),  # zero-based next pointer from UI
    campaign: Optional[str] = Form(None),
    page: int = Form(1),
):
    lead_index_1based = next_index + 1
    background_tasks.add_task(spawn_call, lead_index_1based, campaign)

    url = f"/?page={page}"
    if campaign:
        url += f"&campaign={campaign}"
    return RedirectResponse(url=url, status_code=303)
