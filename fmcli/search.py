from requests_html import HTMLSession
from bs4 import BeautifulSoup
from rich.table import Table
from console_manager import console
from utils import clear_console
import re

BASE_URL = "https://fmstream.org/index.php?s="

def search_stations(query: str, start_index=0):
    """
    Search FMStream stations by query and return:
    - List of stations with name, location, genre, description, and streams
    - Previous page index (or None)
    - Next page index (or None)
    """
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
        name = block.select_one("h3.stn").text.strip() if block.select_one("h3.stn") else "Unknown Station"
        location = block.select_one(".loc").text.strip() if block.select_one(".loc") else "Unknown Location"
        genre = block.select_one(".sty").text.strip() if block.select_one(".sty") else "Unknown Genre"
        desc = block.select_one(".desc").text.strip() if block.select_one(".desc") else ""

        streams = []
        for sq in block.select(".sqdiv .sq"):
            url = sq.get("title")
            codec = sq.select_one(".cn").text.strip() if sq.select_one(".cn") else "Unknown"
            bitrate = sq.select_one(".br").text.strip() + " kbps" if sq.select_one(".br") else "Unknown"
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

    # Pagination
    prev_link = None
    next_link = None
    footer = soup.select_one("footer#footer")
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
    clear_console()
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
