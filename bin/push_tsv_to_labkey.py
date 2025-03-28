#!/usr/bin/env python

import argparse
import datetime
import os
import sys

import polars as pl
import requests
from loguru import logger


class LabKeyUploadError(Exception):
    """
    Exception raised for errors encountered during the LabKey data upload process.
    """


def set_verbosity(verbosity: int, quiet: int) -> None:
    """
    Sets the logging verbosity level based on the counts of verbose (-v) and quiet (-q) flags.

    This function computes an effective verbosity level as the difference between the number
    of verbose flags and quiet flags. It then uses a match-case statement to set the appropriate
    log level for the loguru logger.

    Parameters
    ----------
    verbosity : int
        The number of verbose (-v) flags provided.
    quiet : int
        The number of quiet (-q) flags provided.
    """
    effective_level = verbosity - quiet
    match effective_level:
        case x if x <= -1:
            level = "ERROR"
        case 0:
            level = "WARNING"
        case 1:
            level = "INFO"
        case 2:
            level = "DEBUG"
        case x if x >= 3:
            level = "TRACE"
        case _:
            level = "WARNING"

    # Remove all previously added sinks and add a new sink to stderr with the chosen level.
    logger.remove()
    logger.add(sys.stderr, level=level)
    logger.debug(f"Log level set to {level}")


def upload_data_to_labkey(
    upload_df: pl.DataFrame,
    token: str,
    labkey_url: str,
    container: str,
    query_name: str,
) -> None:
    """
    Uploads data from a Polars DataFrame to a LabKey list using the LabKey API.

    The function first adds an 'upload_time' column with the current UTC time so that new rows
    can be sorted to appear at the top of the list (assuming the LabKey list is configured to sort
    descending by this column). It then converts the DataFrame into a list of dictionaries and
    makes a POST request to LabKey's insertRows API endpoint.

    Parameters
    ----------
    df : pl.DataFrame
        The Polars DataFrame containing the data to be uploaded.
    token : str
        The LabKey API access token used for authentication.
    labkey_url : str
        The base URL of the LabKey server (e.g., "https://yourlabkeyserver.com").
    container : str
        The container path on the LabKey server where the target list is located.
    query_name : str
        The name of the LabKey list (query) to which data will be inserted.

    Raises
    ------
    LabKeyUploadError
        If the API request returns an error status.
    requests.RequestException
        If a network-related error occurs during the API call.
    """
    # Add an 'upload_time' column with the current UTC time.
    current_time = datetime.datetime.utcnow().isoformat()
    upload_df = upload_df.with_columns(pl.lit(current_time).alias("upload_time"))

    # Convert the DataFrame to a list of dictionaries (one per row).
    records = upload_df.to_dicts()

    # Construct the API endpoint URL.
    url = f"{labkey_url.rstrip('/')}/labkey/query/insertRows.api"
    params = {"containerPath": container, "queryName": query_name}

    # Prepare HTTP headers, including the LabKey API access token.
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}

    # Build the payload for the POST request.
    payload = {"rows": records, "apiVersion": 9.1}

    try:
        response = requests.post(url, params=params, json=payload, headers=headers)
    except requests.RequestException as e:
        logger.error(f"Network error during LabKey API request: {e}")
        raise

    if response.status_code != 200:
        logger.error(f"Failed to upload data: {response.status_code} - {response.text}")
        raise LabKeyUploadError(f"Error uploading data: {response.status_code} - {response.text}")

    logger.info("Data uploaded successfully.")


def main() -> None:
    """
    Command-line interface for uploading CSV data to a LabKey list.

    This function parses command-line arguments to obtain the CSV file path and LabKey details,
    retrieves the LabKey API access token from the environment variable 'LABKEY_TOKEN', loads the CSV
    into a Polars DataFrame, sets the logging verbosity, and calls the upload function.
    """
    parser = argparse.ArgumentParser(description="Upload CSV data to a LabKey list using the LabKey API.")
    parser.add_argument("csv_file", help="Path to the CSV file containing the data to upload.")
    parser.add_argument(
        "--labkey-url",
        required=True,
        help="Base URL of the LabKey server (e.g., 'https://yourlabkeyserver.com').",
    )
    parser.add_argument("--container", required=True, help="LabKey container path where the list is located.")
    parser.add_argument("--query-name", required=True, help="Name of the LabKey list (query) to update.")
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Increase verbosity (can be used multiple times).",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="count",
        default=0,
        help="Decrease verbosity (can be used multiple times).",
    )

    args = parser.parse_args()

    # Set the logging verbosity based on -v and -q arguments.
    set_verbosity(args.verbose, args.quiet)

    # Retrieve the LabKey API access token from the environment.
    token = os.getenv("LABKEY_TOKEN")
    if not token:
        logger.error("LABKEY_TOKEN environment variable not set.")
        sys.exit("Error: LABKEY_TOKEN environment variable not set.")

    try:
        # Attempt to load the CSV file into a Polars DataFrame.
        full_tsv_df = pl.read_csv(args.csv_file)
    except FileNotFoundError:
        logger.error(f"CSV file not found: {args.csv_file}")
        sys.exit(f"CSV file not found: {args.csv_file}")

    try:
        upload_data_to_labkey(full_tsv_df, token, args.labkey_url, args.container, args.query_name)
    except LabKeyUploadError as e:
        logger.error(f"LabKey upload failed: {e}")
        sys.exit(f"LabKey upload failed: {e}")
    except requests.RequestException as e:
        logger.error(f"Network error during LabKey API request: {e}")
        sys.exit(f"Network error during LabKey API request: {e}")
    else:
        logger.error("Unknown error encountered when parsing the GOTTCHA2 full TSV report. Aborting.")
        sys.exit(1)


if __name__ == "__main__":
    main()
