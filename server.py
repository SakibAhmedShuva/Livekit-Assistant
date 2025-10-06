# server.py

import os
import uuid
import threading
import subprocess
import flask
from flask_cors import CORS
from dotenv import load_dotenv
from livekit import api

# Load environment variables from .env file
load_dotenv()

LIVEKIT_URL = os.environ.get("LIVEKIT_URL")
LIVEKIT_API_KEY = os.environ.get("LIVEKIT_API_KEY")
LIVEKIT_API_SECRET = os.environ.get("LIVEKIT_API_SECRET")

# This is the room the agent and users will join
ROOM_NAME = "rajesh-portfolio-room"

if not all([LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET]):
    raise EnvironmentError(
        "LIVEKIT_URL, LIVEKIT_API_KEY, and LIVEKIT_API_SECRET must be set"
    )

app = flask.Flask(__name__, template_folder="templates")
# Activate CORS for the token endpoint
CORS(app, resources={r"/get-token": {"origins": "*"}})


@app.route("/")
def index():
    """Serves the frontend HTML"""
    return flask.render_template("index.html")


@app.route("/get-token", methods=["GET"])
def get_token():
    """Generates a Livekit token and returns it with the correct WS URL."""
    identity = f"user-{uuid.uuid4()}"
    
    # Create a token with permissions to join a specific room
    token = (
        api.AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET)
        .with_identity(identity)
        .with_name(f"Visitor-{identity}")
        .with_grants(api.VideoGrants(room_join=True, room=ROOM_NAME))
    )
    
    # Return both the token AND the Livekit URL from the environment
    return flask.jsonify({
        "token": token.to_jwt(),
        "livekitUrl": LIVEKIT_URL
    })


def run_agent_worker():
    """
    Runs the app.py agent worker directly via Python asyncio.
    """
    print("=" * 60)
    print("Starting Livekit Agent worker...")
    print("=" * 60)
    
    try:
        import asyncio
        from app import entrypoint
        from livekit.agents import WorkerOptions, cli
        from livekit import rtc
        
        # Create agent token
        agent_token = (
            api.AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET)
            .with_identity("devraze-agent")
            .with_name("DevRaze")
            .with_grants(api.VideoGrants(
                room_join=True, 
                room=ROOM_NAME, 
                room_admin=True,
            ))
        )
        
        print(f"[AGENT] Connecting to room: {ROOM_NAME}")
        print(f"[AGENT] LiveKit URL: {LIVEKIT_URL}")
        print("=" * 60)
        
        # Run the worker
        worker_opts = WorkerOptions(
            entrypoint_fnc=entrypoint,
            api_key=LIVEKIT_API_KEY,
            api_secret=LIVEKIT_API_SECRET,
            ws_url=LIVEKIT_URL,
        )
        
        # Start the agent using the CLI
        cli.run_app(worker_opts)
            
    except Exception as e:
        print(f"[AGENT ERROR] {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Start the agent worker in a separate thread
    agent_thread = threading.Thread(target=run_agent_worker, daemon=True)
    agent_thread.start()

    # Give agent a moment to start
    import time
    time.sleep(2)

    # Run the Flask app
    print("\n" + "=" * 60)
    print("Starting Flask server...")
    print("=" * 60 + "\n")
    app.run(host="0.0.0.0", port=7860)