from dotenv import load_dotenv

from livekit import agents
from livekit.agents import AgentSession, Agent, RoomInputOptions
from livekit.plugins import (
    noise_cancellation,
)
from livekit.plugins import google
from prompts import ENHANCED_DEMANDIFY_CALLER_INSTRUCTIONS, SESSION_INSTRUCTION
import importlib
import sys
import csv
import os
import logging
from typing import Optional, Tuple, List, Dict
load_dotenv()

# Suppress unsupported option warning (truncate) from Google Realtime API
logging.getLogger("livekit.plugins.google").setLevel(logging.ERROR)


CAMPAIGNS = {
    # name: (module, agent_attr, session_attr)
    "Default (prompts)": ("prompts", "ENHANCED_DEMANDIFY_CALLER_INSTRUCTIONS", "SESSION_INSTRUCTION"),
    "SplashBI (prompts2)": ("prompts2", "ENHANCED_DEMANDIFY_CALLER_INSTRUCTIONS", "SESSION_INSTRUCTION"),
    "KonfHub (prompts3)": ("prompts3", "ENHANCED_DEMANDIFY_CALLER_INSTRUCTIONS", "SESSION_INSTRUCTION"),
    "Zoom Phone (prompts4)": ("prompts4", "ENHANCED_DEMANDIFY_CALLER_INSTRUCTIONS", "SESSION_INSTRUCTION"),
}

CAMPAIGN_OVERRIDE: tuple[str, str, str] | None = None


def _load_campaign_prompts(module_name: str | None = None,
                           agent_attr: str | None = None,
                           session_attr: str | None = None):
    """
    Load campaign-specific prompts from environment variables if provided.
    Env vars:
      - CAMPAIGN_PROMPT_MODULE: python module path (default: 'prompts')
      - CAMPAIGN_AGENT_NAME: constant name for agent instructions (default: 'ENHANCED_DEMANDIFY_CALLER_INSTRUCTIONS')
      - CAMPAIGN_SESSION_NAME: constant name for session instructions (default: 'SESSION_INSTRUCTION')

    Returns: (agent_instructions: str, session_instructions: str)
    """
    module_name = module_name or os.getenv("CAMPAIGN_PROMPT_MODULE", "prompts")
    agent_attr = agent_attr or os.getenv("CAMPAIGN_AGENT_NAME", "ENHANCED_DEMANDIFY_CALLER_INSTRUCTIONS")
    session_attr = session_attr or os.getenv("CAMPAIGN_SESSION_NAME", "SESSION_INSTRUCTION")

    agent_text = ENHANCED_DEMANDIFY_CALLER_INSTRUCTIONS
    session_text = SESSION_INSTRUCTION

    try:
        mod = importlib.import_module(module_name)
        agent_text = getattr(mod, agent_attr, agent_text)
        session_text = getattr(mod, session_attr, session_text)
    except Exception:
        # Fallback to defaults silently
        pass

    return agent_text, session_text


def _select_campaign_from_console() -> tuple[str, str, str] | None:
    """Present a simple console menu to select a campaign. Returns (module, agent_attr, session_attr)
    or None if user chooses to keep env defaults.
    """
    try:
        print("\nSelect Campaign (press Enter to use .env settings):")
        for idx, name in enumerate(CAMPAIGNS.keys(), start=1):
            print(f"  [{idx}] {name}")
        choice = input("Enter number (or press Enter to skip): ").strip()
        if not choice:
            return None
        idx = int(choice)
        if idx < 1 or idx > len(CAMPAIGNS):
            print("Invalid choice. Using .env settings.")
            return None
        name = list(CAMPAIGNS.keys())[idx - 1]
        return CAMPAIGNS[name]
    except Exception:
        # On any error, fall back to env
        return None


def _read_leads(leads_csv: str) -> List[Dict[str, str]]:
    """Read all leads from the CSV as a list of dicts. Returns empty list on error."""
    leads: List[Dict[str, str]] = []
    try:
        with open(leads_csv, mode="r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Normalize keys to expected set and ensure presence
                leads.append({
                    "prospect_name": row.get("prospect_name", "").strip(),
                    "resource_name": row.get("resource_name", "").strip(),
                    "job_title": row.get("job_title", "").strip(),
                    "company_name": row.get("company_name", "").strip(),
                    "email": row.get("email", "").strip(),
                    "phone": row.get("phone", "").strip(),
                    "timezone": row.get("timezone", "").strip(),
                })
    except Exception:
        pass
    return leads


def _select_prospect_from_console(leads: List[Dict[str, str]]) -> Optional[Dict[str, str]]:
    """Console menu to select a single prospect from the list. Returns the selected lead
    or None to use defaults/env.
    """
    if not leads:
        return None
    try:
        print("\nSelect Prospect (press Enter to use .env LEAD_INDEX or first row):")
        for idx, ld in enumerate(leads, start=1):
            name = ld.get("prospect_name", "")
            title = ld.get("job_title", "")
            comp = ld.get("company_name", "")
            phone = ld.get("phone", "")
            print(f"  [{idx}] {name} — {title} @ {comp} — {phone}")
        choice = input("Enter number (or press Enter to skip): ").strip()
        if not choice:
            return None
        i = int(choice)
        if i < 1 or i > len(leads):
            print("Invalid choice. Using defaults.")
            return None
        return leads[i - 1]
    except Exception:
        return None


class Assistant(Agent):
    def __init__(self, instructions_text: str) -> None:
        super().__init__(
            instructions=instructions_text,
            llm=google.beta.realtime.RealtimeModel(
                voice="Leda",
                temperature=0.2,
            ),
            tools=[],
        )


async def entrypoint(ctx: agents.JobContext):
    session = AgentSession(
        
    )

    # Load leads from CSV and determine which prospect to use
    leads_csv = os.getenv("LEADS_CSV_PATH", os.path.join(os.path.dirname(__file__), "leads.csv"))
    all_leads = _read_leads(leads_csv)
    lead: Optional[Dict[str, str]] = None

    # Priority: env index > console selection > first row
    # Use environment variable LEAD_INDEX (1-based) if provided
    try:
        env_idx = os.getenv("LEAD_INDEX")
        if env_idx:
            i = int(env_idx) - 1
            if 0 <= i < len(all_leads):
                lead = all_leads[i]
    except Exception:
        pass
    # If no env index provided or invalid, offer console selection
    if lead is None:
        sel_lead = _select_prospect_from_console(all_leads)
        if sel_lead is not None:
            lead = sel_lead
    # Fallback to first row if still None
    if lead is None and all_leads:
        lead = all_leads[0]

    # Prefer GUI override if set; else offer console selection; else use env
    selection = CAMPAIGN_OVERRIDE or _select_campaign_from_console()
    if selection:
        mod_name, agent_attr, session_attr = selection
        agent_instructions_text, session_instructions_text = _load_campaign_prompts(
            module_name=mod_name,
            agent_attr=agent_attr,
            session_attr=session_attr,
        )
    else:
        # Use environment variables or defaults
        agent_instructions_text, session_instructions_text = _load_campaign_prompts()

    await session.start(
        room=ctx.room,
        agent=Assistant(agent_instructions_text),
        room_input_options=RoomInputOptions(
            # LiveKit Cloud enhanced noise cancellation
            # - If self-hosting, omit this parameter
            # - For telephony applications, use `BVCTelephony` for best results
            video_enabled=False,
            noise_cancellation=noise_cancellation.BVCTelephony(),
        ),
    )

    await ctx.connect()

    # Prepare session instructions with lead details (campaign-specific)
    instructions = session_instructions_text
    if lead:
        # Replace bracket placeholders in the script when present
        def repl(text, placeholder, value):
            return text.replace(placeholder, value) if value else text

        instructions = repl(instructions, "[Prospect Name]", lead.get("prospect_name", "there"))
        instructions = repl(instructions, "[Resource Name]", lead.get("resource_name", "our team"))
        instructions = repl(instructions, "[Job Title]", lead.get("job_title", "your role"))
        instructions = repl(instructions, "[Company Name]", lead.get("company_name", "your company"))
        instructions = repl(instructions, "[____@abc.com]", lead.get("email", "email@domain.com"))

        # Also provide a structured preface the LLM can reference
        instructions = (
            f"Lead Context:\n"
            f"- Prospect Name: {lead.get('prospect_name','')}\n"
            f"- Job Title: {lead.get('job_title','')}\n"
            f"- Company: {lead.get('company_name','')}\n"
            f"- Email: {lead.get('email','')}\n"
            f"- Phone: {lead.get('phone','')}\n"
            f"- Timezone: {lead.get('timezone','')}\n"
            f"- Caller (Resource Name): {lead.get('resource_name','')}\n\n"
        ) + instructions

    await session.generate_reply(
        instructions=instructions,
    )


if __name__ == "__main__":
    # Console-only: run single call session with console-based selections
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))