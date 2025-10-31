import threading
import itertools
import subprocess
import time
from rich.panel import Panel
from rich.live import Live
from rich.console import Console
from utils import get_icy_metadata_robust  # import your robust metadata function

console = Console()

def play_stream_ffplay(stream):
    """
    Play a stream with live metadata:
    - Station name
    - Genre
    - Bitrate
    - Currently playing song
    """
    url = stream["url"]
    stopped = threading.Event()
    animation = itertools.cycle(["▰▱▱▱▱", "▰▰▱▱▱", "▰▰▰▱▱", "▰▰▰▰▱", "▰▰▰▰▰", "▱▰▰▰▰"])

    # Initial metadata
    metadata = {
        "stream_name": stream.get("station_name", "N/A"),
        "stream_genre": stream.get("station_genre", "N/A"),
        "stream_bitrate": stream.get("bitrate", "N/A"),
        "current_title": "Loading..."
    }

    # Launch ffplay
    cmd = ["ffplay", "-nodisp", "-hide_banner", "-autoexit", "-loglevel", "info", "-i", url]
    process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True, bufsize=1)

    # Thread to update metadata every 5 seconds
    def update_metadata():
        while not stopped.is_set():
            meta = get_icy_metadata_robust(url)
            for key in ['stream_name', 'stream_genre', 'stream_bitrate', 'current_title']:
                if meta.get(key):
                    metadata[key] = meta[key]
            time.sleep(5)

    reader_thread = threading.Thread(target=update_metadata, daemon=True)
    reader_thread.start()

    try:
        with Live(console=console, refresh_per_second=5) as live:
            while not stopped.is_set() and process.poll() is None:
                bar = next(animation)
                panel = Panel.fit(
                    f"[bold yellow]▶️ Now Playing:[/]\n"
                    f"[cyan]{metadata.get('stream_name')}[/]\n\n"
                    f"[green]Genre: {metadata.get('stream_genre')}[/]\n"
                    f"[magenta]Bitrate: {metadata.get('stream_bitrate')} kbps[/]\n\n"
                    f"[bold white]♪ {metadata.get('current_title')}[/]\n\n"
                    f"[dim]{bar} Streaming...[/]\n"
                    f"[dim]Press Ctrl+C to stop playback[/]",
                    title="🎧 FMStream Player",
                    border_style="bright_blue"
                )
                live.update(panel)
                time.sleep(0.3)
        process.wait()
        return "done"

    except KeyboardInterrupt:
        console.print("\n[red]⏹️ Stopping playback...[/]")
        stopped.set()
        try:
            process.terminate()
            process.wait(timeout=3)
        except Exception:
            pass
        return "stopped"
