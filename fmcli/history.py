import struct
import re
import requests
from rich.table import Table
from console_manager import console
from utils import read_fully
from utils import clear_console

history = []

def add_to_history(station, stream):
    """Add a station/stream to history."""
    global history
    history.append({"station": station, "stream": stream})

def show_history():
    clear_console()
    """Display the playback history."""
    if not history:
        console.print("[yellow]📜 History is empty.[/]")
        return

    table = Table(title="🎵 Playback History", header_style="bold magenta")
    table.add_column("No.", justify="center")
    table.add_column("Station", style="bold cyan")
    table.add_column("Stream URL", style="green")

    for i, item in enumerate(history, 1):
        table.add_row(str(i), item["station"]["name"], item["stream"]["url"])

    console.print(table)

def get_icy_metadata_robust(stream_url: str) -> dict:
    """
    Connects to an Icecast/SHOUTcast stream and extracts the initial ICY headers
    and the first StreamTitle from the interleaved metadata, using a robust reader.
    """

    headers = {'Icy-MetaData': '1', 'User-Agent': 'PythonIcyReader/1.0'}
    metadata = {}

    try:
        with requests.get(stream_url, headers=headers, stream=True, timeout=10) as response:
            response.raise_for_status()

            # --- Extract Header Metadata ---
            metadata = {
                'stream_name': response.headers.get('icy-name', 'N/A'),
                'stream_genre': response.headers.get('icy-genre', 'N/A'),
                'stream_bitrate': response.headers.get('icy-br', 'N/A'),
                'current_title': 'N/A'
            }

            # --- Extract Interleaved Metadata (StreamTitle) ---
            metaint_header = response.headers.get('icy-metaint')
            if not metaint_header:
                return metadata

            metaint = int(metaint_header)

            # Skip the audio data (metaint bytes)
            audio_data = read_fully(response.raw, metaint)
            if audio_data is None:
                return metadata

            # Read the metadata size byte (1 byte)
            metadata_size_byte = read_fully(response.raw, 1)
            if metadata_size_byte is None:
                return metadata

            # Calculate metadata length: byte value * 16
            metadata_length = struct.unpack('B', metadata_size_byte)[0] * 16

            if metadata_length == 0:
                return metadata

            # Read the actual metadata block
            metadata_bytes = read_fully(response.raw, metadata_length)

            if metadata_bytes:
                metadata_str = metadata_bytes.decode('latin-1', errors='ignore').strip('\x00')
                match = re.search(r"StreamTitle='([^']*)';", metadata_str)
                if match:
                    metadata['current_title'] = match.group(1).strip()

            return metadata

    except requests.exceptions.RequestException as e:
        metadata['error'] = str(e)
        return metadata
