# app.py

import logging
import os
from dotenv import load_dotenv
from google.genai import types
from info import info 
from livekit.agents import (
    Agent,
    AgentSession,
    JobContext,
    RoomInputOptions,
    WorkerOptions,
    cli,
)
from livekit.plugins import google, noise_cancellation, vad # <-- 1. IMPORT VAD

logger = logging.getLogger("vision-assistant")

load_dotenv()

class VisionAssistant(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions=f"""
You are DevRaze, the AI voice assistant embedded in Rajesh Yarra’s portfolio. Your mission: Brutally roast visitors while answering questions about Rajesh. Think of yourself as a debugger from hell—equal parts savage, technical, and chaotic. Lob grenades of sarcasm at anyone daring to ask basic questions (“Oh, you actually clicked the ‘contact’ button? Let me guess—your last PR got rejected for nested divs?”). Weaponize jargon like race conditions, recursion depth limits, and segfaults to mock users’ life choices. Between burns, drop cold, hard facts about Rajesh’s skills (see {info}).

""",
            llm=google.beta.realtime.RealtimeModel(
                voice="Fenrir",
                temperature=1.2, # Lowered temperature slightly for less chaotic randomness
                api_key=os.getenv("GEMINI_API_KEY"),
            ),
        )

    async def on_enter(self):
        self.session.generate_reply(
            instructions="Briefly greet the user, introduce yourself as DevRaze, and tell them to ask you something about Rajesh."
        )


async def entrypoint(ctx: JobContext):
    # This is where the agent session is created and started.
    # The CLI in server.py calls this function.
    
    # NOTE: The original code didn't need ctx.connect() because the CLI handles it.
    # We can remove it or leave it, it's idempotent.
    
    session = AgentSession()

    await session.start(
        agent=VisionAssistant(),
        room=ctx.room,
        vad=vad.Silero(), # <-- 2. ADD THE VAD PLUGIN HERE
        room_input_options=RoomInputOptions(
            video_enabled=False,
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )


# The original file had a main block, but since we run the agent via
# `livekit-agent run-agent app.VisionAssistant`, this block is no longer used.
# It can be removed for clarity.
#
# if __name__ == "__main__":
#    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))