import threading
import itertools
import subprocess
import time
import sys
import termios
import tty
import select
import signal
from rich.panel import Panel
from rich.live import Live
from rich.console import Console
from utils import get_icy_metadata_robust  # your robust metadata fetcher

console = Console()

# ---------- Stream Control Functions ----------

def pause_stream_ffplay(process, paused_event, status):
    """Pause ffplay playback."""
    if process.poll() is None and not paused_event.is_set():
        process.send_signal(signal.SIGSTOP)
        paused_event.set()
        status["state"] = "paused"
        # console.print("[yellow]⏸️ Paused[/]")

def resume_stream_ffplay(process, paused_event, status):
    """Resume ffplay playback."""
    if process.poll() is None and paused_event.is_set():
        process.send_signal(signal.SIGCONT)
        paused_event.clear()
        status["state"] = "playing"
        # console.print("[green]▶️ Resumed[/]")

def stop_stream_ffplay(process, stopped_event, status):
    """Stop ffplay playback."""
    if process.poll() is None:
        # console.print("[red]⏹️ Stopping playback...[/]")
        stopped_event.set()
        status["state"] = "stopped"
        process.terminate()
        try:
            process.wait(timeout=2)
        except Exception:
            process.kill()

# ---------- Key Input Handling ----------

def read_key_nonblocking():
    """Read a single key without blocking."""
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setcbreak(fd)
        if sys.stdin in select.select([sys.stdin], [], [], 0.1)[0]:
            return sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return None

def handle_key_input(process, stopped_event, paused_event, status):
    """
    Listen for key presses:
      p = pause
      r = resume
      s = stop
      b = back
    """
    while not stopped_event.is_set():
        key = read_key_nonblocking()
        if not key:
            continue

        if key.lower() == "p":
            pause_stream_ffplay(process, paused_event, status)
        elif key.lower() == "r":
            resume_stream_ffplay(process, paused_event, status)
        elif key.lower() == "s":
            stop_stream_ffplay(process, stopped_event, status)
        elif key.lower() == "b":
            console.print("[blue]⬅️ Returning to main menu...[/]")
            stop_stream_ffplay(process, stopped_event, status)
            break

# ---------- Main Player Function ----------

def play_stream_ffplay(stream):
    """
    Play a stream with live metadata and interactive controls:
    p = pause, r = resume, s = stop, b = back
    """
    url = stream["url"]
    stopped = threading.Event()
    paused = threading.Event()
    animation = itertools.cycle(["▰▱▱▱▱", "▰▰▱▱▱", "▰▰▰▱▱", "▰▰▰▰▱", "▰▰▰▰▰", "▱▰▰▰▰"])

    metadata = {
        "stream_name": stream.get("station_name", "N/A"),
        "stream_genre": stream.get("station_genre", "N/A"),
        "stream_bitrate": stream.get("bitrate", "N/A"),
        "current_title": "Loading..."
    }

    # Shared status dictionary for live updates
    status = {"state": "playing"}

    # Launch ffplay
    cmd = ["ffplay", "-nodisp", "-hide_banner", "-autoexit", "-loglevel", "info", "-i", url]
    process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True, bufsize=1)

    # Metadata updater thread
    def update_metadata():
        while not stopped.is_set():
            meta = get_icy_metadata_robust(url)
            for key in ['stream_name', 'stream_genre', 'stream_bitrate', 'current_title']:
                if meta.get(key):
                    metadata[key] = meta[key]
            time.sleep(5)

    threading.Thread(target=update_metadata, daemon=True).start()
    threading.Thread(target=handle_key_input, args=(process, stopped, paused, status), daemon=True).start()

    try:
        with Live(console=console, refresh_per_second=5) as live:
            while not stopped.is_set() and process.poll() is None:
                bar = next(animation)

                # Determine status color and label
                state = status["state"]
                if state == "playing":
                    state_label = "[green]▶️ Playing[/]"
                elif state == "paused":
                    state_label = "[yellow]⏸️ Paused[/]"
                else:
                    state_label = "[red]⏹️ Stopped[/]"

                panel = Panel.fit(
                    f"{state_label}\n\n"
                    f"[cyan]{metadata.get('stream_name')}[/]\n"
                    f"[green]Genre: {metadata.get('stream_genre')}[/]\n"
                    f"[magenta]Bitrate: {metadata.get('stream_bitrate')} kbps[/]\n\n"
                    f"[bold white]♪ {metadata.get('current_title')}[/]\n\n"
                    f"[dim]{bar} Streaming...[/]\n"
                    f"[dim]Controls: (p) Pause  (r) Resume  (s) Stop  (b) Back[/]",
                    title="🎧 FMStream Player",
                    border_style="bright_blue"
                )
                live.update(panel)
                time.sleep(0.3)

        process.wait()
        status["state"] = "stopped"
        return "done"

    except KeyboardInterrupt:
        stop_stream_ffplay(process, stopped, status)
        return "stopped"
