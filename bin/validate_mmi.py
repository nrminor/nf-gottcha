#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse

import requests
import typer
from requests.adapters import HTTPAdapter, Retry

app = typer.Typer()


def is_url(input_str: str) -> bool:
    """
    Returns True if the input string has an HTTP or HTTPS scheme.
    """
    parsed = urlparse(input_str)
    return parsed.scheme in ("http", "https")


def download_url(url: str, dest: Path) -> None:
    """
    Downloads a file from a URL using a requests Session with retries.
    Saves the content to the destination path.
    """
    session = requests.Session()
    # Configure retry strategy for common transient errors.
    retries = Retry(
        total=5,
        backoff_factor=1,
        status_forcelist=[500, 502, 503, 504],
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    try:
        response = session.get(url, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        typer.echo(f"Error downloading file from URL: {url}\nError: {e}")
        raise typer.Exit(code=1)  # noqa: B904

    try:
        dest.write_bytes(response.content)
        typer.echo(f"Downloaded file from {url} to {dest}")
    except Exception as e:  # noqa: BLE001
        typer.echo(f"Error writing downloaded content to {dest}\nError: {e}")
        raise typer.Exit(code=1)  # noqa: B904


@app.command()
def main(source: str, dest: str | None = None) -> None:
    """
    Determine if SOURCE is a URL or file path.

    If SOURCE is a URL, download the content.
    If DEST is not provided, the file name is derived from the URL.

    If SOURCE is a file path, validate that it exists and is a file.
    """
    if is_url(source):
        typer.echo(f"Detected URL: {source}")
        # Derive destination filename if not provided.
        if dest is None:
            parsed = urlparse(source)
            filename = Path(parsed.path).name
            if not filename:
                typer.echo("Error: Unable to determine a file name from the URL. Please provide a --dest option.")
                raise typer.Exit(code=1)
            dest = filename
        dest_path = Path(dest)
        download_url(source, dest_path)
    else:
        # Assume SOURCE is a file path.
        path = Path(source)
        if not path.exists():
            typer.echo(f"Error: The file path '{source}' does not exist.")
            raise typer.Exit(code=1)
        if not path.is_file():
            typer.echo(f"Error: The path '{source}' is not a file.")
            raise typer.Exit(code=1)
        typer.echo(f"File path '{source}' is valid.")


if __name__ == "__main__":
    app()
