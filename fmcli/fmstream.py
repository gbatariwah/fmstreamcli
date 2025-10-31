import re
import sys
import time
import threading
import subprocess
import itertools
import os
import requests
from requests_html import HTMLSession
from bs4 import BeautifulSoup
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt
from rich.panel import Panel
from rich.live import Live

console = Console()
BASE_URL = "https://fmstream.org/index.php?s="
history = []

def clear_console():
    os.system("cls" if os.name == "nt" else "clear")


def search_stations(query: str, start_index=0):
    """Search stations and return stations list and pagination links."""
    session = HTMLSession()
    try:
        url = f"{BASE_URL}{query}&n={start_index}"
        resp = session.get(url)
        resp.html.render(timeout=20)
    except Exception as e:
        console.print(f"[red]❌ Failed to render page:[/] {e}")
        return [], None, None

    soup = BeautifulSoup(resp.html.html, "html.parser")
    stations = []

    for block in soup.select("div.stnblock"):
        name = block.select_one("h3.stn")
        name = name.text.strip() if name else "Unknown Station"
        location = block.select_one(".loc")
        location = location.text.strip() if location else "Unknown Location"
        genre = block.select_one(".sty")
        genre = genre.text.strip() if genre else "Unknown Genre"
        desc = block.select_one(".desc")
        desc = desc.text.strip() if desc else ""

        streams = []
        for sq in block.select(".sqdiv .sq"):
            url = sq.get("title")
            codec_div = sq.select_one(".cn")
            bitrate_div = sq.select_one(".br")
            codec = codec_div.text.strip() if codec_div else "Unknown"
            bitrate = bitrate_div.text.strip() + " kbps" if bitrate_div else "Unknown"
            if url:
                streams.append({"url": url, "codec": codec, "bitrate": bitrate})

        if streams:
            stations.append({
                "name": name,
                "location": location,
                "genre": genre,
                "description": desc,
                "streams": streams
            })

    # Pagination links
    footer = soup.select_one("footer#footer")
    prev_link = None
    next_link = None
    if footer:
        prev_tag = footer.select_one('a.btn.arrbtn:contains("←")')
        next_tag = footer.select_one('a.btn.arrbtn:contains("→")')
        if prev_tag and "n=" in prev_tag.get("href", ""):
            prev_link = int(re.search(r"n=(\d+)", prev_tag["href"]).group(1))
        if next_tag and "n=" in next_tag.get("href", ""):
            next_link = int(re.search(r"n=(\d+)", next_tag["href"]).group(1))

    return stations, prev_link, next_link


def show_station_list(stations):
    clear_console()
    table = Table(title="FMStream Search Results", show_header=True, header_style="bold magenta")
    table.add_column("No.", justify="center", width=4)
    table.add_column("Station Name", style="bold cyan")
    table.add_column("Genre", style="green")
    table.add_column("Location", style="yellow")

    for i, st in enumerate(stations, 1):
        table.add_row(str(i), st["name"], st["genre"], st["location"])

    console.print(table)


def show_streams(station):
    # Sort streams by bitrate ascending
    def parse_bitrate(b):
        try:
            return int(b['bitrate'].replace(" kbps", ""))
        except:
            return 0  # Unknown bitrate goes first

    sorted_streams = sorted(station["streams"], key=parse_bitrate)

    table = Table(title=f"Streams for {station['name']}", header_style="bold blue")
    table.add_column("No.", justify="center", width=4)
    table.add_column("Codec", style="cyan", width=10)
    table.add_column("Bitrate", style="yellow", width=10)
    table.add_column("Stream URL", style="bold white")

    for i, s in enumerate(sorted_streams, 1):
        table.add_row(str(i), s["codec"], s["bitrate"], s["url"])

    console.print(table)



def get_icy_title_from_metadata(metadata_bytes: bytes) -> str | None:
    metadata_str = metadata_bytes.decode('latin-1', errors='ignore').strip('\x00')
    match = re.search(r"StreamTitle='([^']*)';", metadata_str)
    if match:
        return match.group(1).strip()
    return None


def fetch_icy_metadata(url, metadata_dict, stopped_event):
    last_title = ""
    headers = {"Icy-MetaData": "1", "User-Agent": "VLC/3.0"}
    while not stopped_event.is_set():
        try:
            r = requests.get(url, headers=headers, stream=True, timeout=10)
            metaint = r.headers.get('icy-metaint')
            if not metaint:
                icy_name = r.headers.get("icy-name")
                if icy_name and icy_name != last_title:
                    metadata_dict["now_playing"] = f"Station: {icy_name}"
                    last_title = icy_name
                r.close()
                time.sleep(5)
                continue
            metaint = int(metaint)
            r.raw.read(metaint, decode_content=False)
            size_byte = r.raw.read(1, decode_content=False)
            if not size_byte:
                r.close()
                continue
            metadata_length = int.from_bytes(size_byte, 'little') * 16
            metadata_bytes = r.raw.read(metadata_length, decode_content=False)
            r.close()
            if metadata_bytes:
                title = get_icy_title_from_metadata(metadata_bytes)
                if title and title != last_title:
                    metadata_dict["now_playing"] = title
                    last_title = title
        except:
            pass
        time.sleep(5)


def play_stream_ffplay(url: str, station_name: str):
    metadata = {"now_playing": "Loading..."}
    stopped = threading.Event()
    animation = itertools.cycle(["▰▱▱▱▱", "▰▰▱▱▱", "▰▰▰▱▱", "▰▰▰▰▱", "▰▰▰▰▰", "▱▰▰▰▰"])

    cmd = ["ffplay", "-nodisp", "-hide_banner", "-autoexit", "-loglevel", "info", "-i", url]
    process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True, bufsize=1)

    reader_thread = threading.Thread(target=fetch_icy_metadata, args=(url, metadata, stopped), daemon=True)
    reader_thread.start()

    try:
        with Live(console=console, refresh_per_second=5) as live:
            while not stopped.is_set() and process.poll() is None:
                bar = next(animation)
                panel = Panel.fit(
                    f"[bold yellow]▶️  Now Playing:[/] [cyan]{station_name}[/]\n\n"
                    f"[bold green]♪ {metadata['now_playing']}[/]\n\n"
                    f"[bold magenta]{bar}[/] [dim](Streaming...)[/]\n\n"
                    f"[dim]Press Ctrl+C to stop playback[/]",
                    title="🎧 FMStream Player",
                    border_style="bright_blue",
                )
                live.update(panel)
                time.sleep(0.3)
        process.wait()
        return "done"
    except KeyboardInterrupt:
        console.print("\n[red]⏹️  Stopping playback...[/]")
        stopped.set()
        try:
            process.terminate()
            process.wait(timeout=3)
        except Exception:
            pass
        return "stopped"


def main():
    global history
    history = []

    while True:
        clear_console()
        console.print(
            Panel("🎧 [bold magenta]FMStream Radio CLI[/]\n(s) Search stations  (h) History  (q) Quit",
                  border_style="bright_magenta"),
        )

        action = Prompt.ask("[bold green]Choose an action[/] (s) Search | (h) History | (q) Quit)").strip().lower()

        if action == "q":
            console.print("[yellow]👋 Exiting player.[/]")
            break
        elif action == "s":
            query = Prompt.ask("[bold green]Enter station name (b=back)[/]").strip()
            if query.lower() == "b":
                continue
            start_index = 0
            while True:
                results, prev_link, next_link = search_stations(query, start_index)
                if not results:
                    console.print("[red]❌ No stations found.[/]")
                    time.sleep(2)
                    break

                show_station_list(results)
                options = "[bold cyan]Select a station number[/] (b=back)"
                if prev_link is not None:
                    options += " (p) Previous"
                if next_link is not None:
                    options += " (n) Next"
                choice = Prompt.ask(options).strip().lower()

                if choice == "b":
                    break
                if choice == "p" and prev_link is not None:
                    start_index = prev_link
                    continue
                if choice == "n" and next_link is not None:
                    start_index = next_link
                    continue
                if not choice.isdigit() or not (1 <= int(choice) <= len(results)):
                    console.print("[red]❌ Invalid choice.[/]")
                    time.sleep(1)
                    continue

                station = results[int(choice) - 1]

                while True:
                    show_streams(station)
                    stream_choice = Prompt.ask("[bold cyan]Select stream number to play (b=back)[/]").strip().lower()
                    if stream_choice == "b":
                        break
                    if not stream_choice.isdigit() or not (1 <= int(stream_choice) <= len(station["streams"])):
                        console.print("[red]❌ Invalid stream choice.[/]")
                        time.sleep(1)
                        continue

                    stream = station["streams"][int(stream_choice) - 1]
                    history.append({"station": station, "stream": stream})
                    play_stream_ffplay(stream["url"], station["name"])
                    console.print("[yellow]🎵 Playback stopped. You can choose another stream or go back.[/]")

        elif action == "h":
            while True:
                if not history:
                    console.print("[yellow]📜 History is empty.[/]")
                    time.sleep(2)
                    break

                table = Table(title="🎵 Playback History", header_style="bold magenta")
                table.add_column("No.", justify="center")
                table.add_column("Station", style="bold cyan")
                table.add_column("Stream URL", style="green")

                for i, item in enumerate(history, 1):
                    table.add_row(str(i), item["station"]["name"], item["stream"]["url"])
                console.print(table)
                Prompt.ask("[dim]Press Enter to go back[/]")
                break

        else:
            console.print("[red]❌ Invalid option.[/]")
            time.sleep(1)


if __name__ == "__main__":
    sys.stdout.reconfigure(line_buffering=True)
    main()
