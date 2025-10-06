# server.py

import os
import uuid
import flask
from flask_cors import CORS
from dotenv import load_dotenv
from livekit import api
import multiprocessing

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


def run_agent_worker_process():
    """
    Runs the agent worker in a separate process.
    This must run in its own process so plugins can be registered on the main thread of that process.
    """
    print("=" * 60)
    print("[AGENT PROCESS] Starting LiveKit Agent worker...")
    print("=" * 60)
    
    try:
        from app import entrypoint
        from livekit.agents import WorkerOptions, cli
        
        print(f"[AGENT PROCESS] Connecting to: {LIVEKIT_URL}")
        print(f"[AGENT PROCESS] Room: {ROOM_NAME}")
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
    # Start the agent worker in a separate PROCESS (not thread)
    agent_process = multiprocessing.Process(target=run_agent_worker_process, daemon=True)
    agent_process.start()

    print("\n" + "=" * 60)
    print("[FLASK] Starting Flask server...")
    print("=" * 60 + "\n")
    
    # Run the Flask app
    app.run(host="0.0.0.0", port=7860)