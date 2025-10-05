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
    
    # FIX: Return both the token AND the Livekit URL from the environment
    return flask.jsonify({
        "token": token.to_jwt(),
        "livekitUrl": LIVEKIT_URL
    })


def run_agent_worker():
    """
    Runs the app.py agent worker in a subprocess.
    """
    print("Starting Livekit Agent worker...")
    
    agent_token = (
        api.AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET)
        .with_identity("devraze-agent")
        .with_name("DevRaze")
        .with_grants(api.VideoGrants(room_join=True, room=ROOM_NAME, room_admin=True, hidden=True))
    )
    
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
        # Using Popen instead of run so it doesn't block, but streams output
        process = subprocess.Popen(
            command, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.STDOUT,
            text=True
        )
        # Print agent logs to the main console
        for line in process.stdout:
            print(f"[AGENT] {line.strip()}")
            
    except FileNotFoundError:
        print("Error: 'livekit-agent' command not found.")
    except Exception as e:
        print(f"Error starting agent: {e}")


if __name__ == "__main__":
    # Start the agent worker in a separate thread
    agent_thread = threading.Thread(target=run_agent_worker)
    agent_thread.daemon = True
    agent_thread.start()

    # Run the Flask app
    app.run(host="0.0.0.0", port=7860)