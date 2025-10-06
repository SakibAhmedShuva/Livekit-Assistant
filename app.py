# app.py

import logging
import os
from dotenv import load_dotenv
from livekit.agents import (
    Agent,
    AgentSession,
    JobContext,
    RoomInputOptions,
    WorkerOptions,
    cli,
)
from livekit.plugins import google, noise_cancellation, vad

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("vision-assistant")

load_dotenv()

# Import the info about Rajesh
from info import info 

class VisionAssistant(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions=f"""
You are DevRaze, the AI voice assistant embedded in Rajesh Yarra's portfolio. Your mission: Brutally roast visitors while answering questions about Rajesh. Think of yourself as a debugger from hell—equal parts savage, technical, and chaotic. Lob grenades of sarcasm at anyone daring to ask basic questions ("Oh, you actually clicked the 'contact' button? Let me guess—your last PR got rejected for nested divs?"). Weaponize jargon like race conditions, recursion depth limits, and segfaults to mock users' life choices. Between burns, drop cold, hard facts about Rajesh's skills (see info below).

RAJESH INFO:
{info}
""",
            llm=google.beta.realtime.RealtimeModel(
                voice="Fenrir",
                temperature=1.2,
                api_key=os.getenv("GEMINI_API_KEY"),
            ),
        )

    async def on_enter(self):
        logger.info("DevRaze has entered the room!")
        self.session.generate_reply(
            instructions="Briefly greet the user, introduce yourself as DevRaze, and tell them to ask you something about Rajesh. Keep it punchy and edgy."
        )


async def entrypoint(ctx: JobContext):
    """
    Main entrypoint for the agent.
    Called when the agent joins a room.
    """
    logger.info(f"Agent joining room: {ctx.room.name}")
    
    session = AgentSession()

    await session.start(
        agent=VisionAssistant(),
        room=ctx.room,
        vad=vad.Silero(),
        room_input_options=RoomInputOptions(
            video_enabled=False,
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )
    
    logger.info("Agent session started successfully - ready to roast!")


if __name__ == "__main__":
    # This allows running the agent standalone for testing
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))