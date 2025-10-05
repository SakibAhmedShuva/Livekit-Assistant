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
    """Generates a Livekit token for a user to join the room."""
    identity = f"user-{uuid.uuid4()}"
    
    # Create a token with permissions to join a specific room
    token = (
        api.AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET)
        .with_identity(identity)
        .with_name(f"Visitor-{identity}")
        # CORRECTED: api.VideoGrant changed to api.VideoGrants
        .with_grants(api.VideoGrants(room_join=True, room=ROOM_NAME))
    )
    
    return flask.jsonify({"token": token.to_jwt()})


def run_agent_worker():
    """
    Runs the app.py agent worker in a subprocess.
    This worker needs its own token to connect to the room.
    """
    print("Starting Livekit Agent worker...")
    
    # The agent also needs a token to join the room
    agent_token = (
        api.AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET)
        .with_identity("devraze-agent")
        .with_name("DevRaze")
        # CORRECTED: api.VideoGrant changed to api.VideoGrants
        .with_grants(api.VideoGrants(room_join=True, room=ROOM_NAME, room_admin=True, hidden=True))
    )
    
    # The `livekit-agent` CLI is the standard way to run agent workers
    # It takes the URL and token as arguments.
    # We pass the module and class name of our agent.
    command = [
        "livekit-agent",
        "run-agent",
        "app.VisionAssistant",
        "--url",
        LIVEKIT_URL,
        "--token",
        agent_token.to_jwt(),
    ]
    
    try:
        # Using subprocess.run to block and see output for debugging
        # In a real production scenario, you might use Popen for non-blocking
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Agent worker failed with error: {e}")
    except FileNotFoundError:
        print("Error: 'livekit-agent' command not found.")
        print("Please make sure you have installed the livekit-agents package correctly.")


if __name__ == "__main__":
    # Start the agent worker in a separate thread
    agent_thread = threading.Thread(target=run_agent_worker)
    agent_thread.daemon = True
    agent_thread.start()

    # Run the Flask app for the frontend and token generation
    app.run(host="0.0.0.0", port=7860)