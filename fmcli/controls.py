# controls.py
import readchar


def handle_player_controls():
    """
    Waits for user key input to control playback.
    Controls:
      p - Play
      a - Pause
      s - Stop
      b - Back / Go to previous menu
    Returns the action as a string.
    """
    print("\nPress a key: [p] Play  [a] Pause  [s] Stop  [b] Back")

    while True:
        key = readchar.readkey().lower()

        if key == "p":
            return "play"
        elif key == "a":
            return "pause"
        elif key == "s":
            return "stop"
        elif key == "b":
            return "back"
        else:
            print("Invalid key! Press p, a, s, or b.")
