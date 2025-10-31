import os
from console_manager import console
import requests
import re
import struct


def clear_console():
    os.system("cls" if os.name == "nt" else "clear")


# Helper function to read a specific number of bytes, handling incomplete reads
def read_fully(raw_stream, size):
    """Reads exactly 'size' bytes from the raw stream, handling partial reads."""
    data = b''
    while len(data) < size:
        chunk = raw_stream.read(size - len(data), decode_content=False)
        if not chunk:
            # Stream closed unexpectedly
            return None
        data += chunk
    return data


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

            # 1. Skip the audio data (metaint bytes)
            audio_data = read_fully(response.raw, metaint)
            if audio_data is None:
                return metadata

            # 2. Read the metadata size byte (1 byte)
            metadata_size_byte = read_fully(response.raw, 1)
            if metadata_size_byte is None:
                return metadata

            # Calculate metadata length: byte value * 16
            metadata_length = struct.unpack('B', metadata_size_byte)[0] * 16

            if metadata_length == 0:
                return metadata

            # 3. Read the actual metadata block
            metadata_bytes = read_fully(response.raw, metadata_length)

            if metadata_bytes:
                # ICY metadata is usually encoded in 'latin-1' (ISO-8859-1)
                metadata_str = metadata_bytes.decode('latin-1', errors='ignore').strip('\x00')

                # Regex to extract the StreamTitle
                match = re.search(r"StreamTitle='([^']*)';", metadata_str)
                if match:
                    metadata['current_title'] = match.group(1).strip()

            return metadata

    except requests.exceptions.RequestException as e:
        metadata['error'] = str(e)
        return metadata
