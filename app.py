from backend import create_app
from backend.extensions import socketio

app = create_app()


if __name__ == "__main__":
    # Disable reloader on Windows to prevent WinError 10038 with SocketIO
    socketio.run(app, host="0.0.0.0", port=5000, allow_unsafe_werkzeug=True, use_reloader=False)

