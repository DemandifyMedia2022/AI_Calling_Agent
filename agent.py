from dotenv import load_dotenv

from livekit import agents
from livekit.agents import AgentSession, Agent, RoomInputOptions
from livekit.plugins import (
    noise_cancellation,
)
from livekit.plugins import google
from prompts import AGENT_INSTRUCTION, SESSION_INSTRUCTION
import csv
import os
import logging
load_dotenv()

# Suppress unsupported option warning (truncate) from Google Realtime API
logging.getLogger("livekit.plugins.google").setLevel(logging.ERROR)


class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions=AGENT_INSTRUCTION,
            llm=google.beta.realtime.RealtimeModel(
            voice="Zephyr",
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

    await session.start(
        room=ctx.room,
        agent=Assistant(),
        room_input_options=RoomInputOptions(
            # LiveKit Cloud enhanced noise cancellation
            # - If self-hosting, omit this parameter
            # - For telephony applications, use `BVCTelephony` for best results
            video_enabled=False,
            noise_cancellation=noise_cancellation.BVCTelephony(),
        ),
    )

    await ctx.connect()

    # Prepare session instructions with lead details
    instructions = SESSION_INSTRUCTION
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
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))