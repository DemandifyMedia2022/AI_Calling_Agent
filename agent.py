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
import tkinter as tk
import csv
import os
import logging
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


def _launch_campaign_gui() -> tuple[str, str, str] | None:
    """Open a tiny Tkinter window with buttons to choose a campaign.
    Returns (module, agent_attr, session_attr) or None if the window is closed without a selection.
    """
    try:
        root = tk.Tk()
        root.title("Select Campaign")
        root.geometry("360x240")
        root.resizable(False, False)

        selection: dict[str, tuple[str, str, str] | None] = {"value": None}

        tk.Label(root, text="Choose a campaign:", font=("Segoe UI", 11, "bold")).pack(pady=10)

        def on_select(name: str):
            selection["value"] = CAMPAIGNS[name]
            root.destroy()

        for name in CAMPAIGNS.keys():
            tk.Button(root, text=name, width=30, command=lambda n=name: on_select(n)).pack(pady=4)

        def use_env():
            selection["value"] = None
            root.destroy()

        tk.Button(root, text="Use .env settings", width=30, command=use_env).pack(pady=8)

        root.mainloop()
        return selection["value"]
    except Exception:
        return None


class Assistant(Agent):
    def __init__(self, instructions_text: str) -> None:
        super().__init__(
            instructions=instructions_text,
            llm=google.beta.realtime.RealtimeModel(
                voice="Leda",
                temperature=0.5,
            ),
            tools=[],
        )
        


async def entrypoint(ctx: agents.JobContext):
    session = AgentSession(
        
    )

    # Load the next lead from CSV
    leads_csv = os.getenv("LEADS_CSV_PATH", os.path.join(os.path.dirname(__file__), "leads.csv"))
    lead = None
    try:
        with open(leads_csv, mode="r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            lead = next(reader, None)
    except FileNotFoundError:
        lead = None
    except Exception:
        lead = None

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
            # noise_cancellation=noise_cancellation.BVCTelephony(),
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
    # If started with `gui`, show a small selection window first.
    if len(sys.argv) > 1 and sys.argv[1].lower() == "gui":
        sel = _launch_campaign_gui()
        if sel:
            CAMPAIGN_OVERRIDE = sel  # type: ignore[assignment]
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))