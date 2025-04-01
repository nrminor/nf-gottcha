import subprocess
from enum import Enum
from pathlib import Path

import typer

app = typer.Typer(context_settings={"help_option_names": ["-h", "--help"]})


# Define the valid Nextflow profiles using an Enum.
class Profile(str, Enum):
    standard = "standard"
    docker = "docker"
    singularity = "singularity"
    apptainer = "apptainer"
    chtc_hpc = "chtc_hpc"
    containerless = "containerless"


# Hard-coded Nextflow parameters based on your nextflow.config.
PARAMS = {
    "illumina_fastq_dir": None,
    "nanopore_fastq_dir": None,
    "ref_mmi": None,
    "ref_mmi_cache": "${launchDir}/ref_mmi_cache",
    "gottcha2_cpus": 8,
    "min_cov": 0.005,
    "min_reads": 3,
    "min_len": 60,
    "max_Zscore": 30,
    "match_factor": 0.5,
    "results": "${launchDir}/results",
    "setup_results": "params.results + '/00_setup'",
    "gottcha_results": "params.results + '/01_gottcha2'",
    "gottcha_sam": "params.gottcha_results + '/01_sam_files'",
    "gottcha_stats": "params.gottcha_results + '/02_stats_tsvs'",
    "gottcha_fasta": "params.gottcha_results + '/03_representative_seqs'",
}


def check_path(value: str, arg_name: str) -> None:
    """
    Check that a provided path exists and is a file or directory.
    Skip checking if the value looks dynamic (e.g. contains '${' or 'params').
    """
    if value and not (value.startswith("${") or "params" in value):
        p = Path(value)
        assert p.exists(), (
            f"Error: The provided {arg_name} path '{value}' does not exist. Please provide a valid file or directory."
        )


@app.command()
def list_profiles() -> None:
    """
    List all available Nextflow profiles.
    """
    typer.echo("Available Nextflow Profiles:")
    for profile in Profile:
        typer.echo(f" - {profile.value}")


@app.command()
def list_params() -> None:
    """
    List all available Nextflow parameters.
    """
    typer.echo("Available Nextflow Parameters:")
    for key, value in PARAMS.items():
        typer.echo(f" - {key} = {value}")


@app.command()
def run(  # noqa: PLR0913
    profile: Profile = typer.Option(  # noqa: B008
        Profile.containerless,
        "--profile",
        "-r",
        help="Nextflow profile to use (default: containerless)",
    ),
    config: str = typer.Option(
        "",
        "--config",
        "-c",
        help="Path to an additional Nextflow configuration file",
    ),
    params_file: str = typer.Option(
        "",
        "--params-file",
        "-p",
        help="Path to an additional Nextflow parameters file",
    ),
    illumina_fastq_dir: str = typer.Option(
        None,
        help="Illumina fastq directory",
    ),
    nanopore_fastq_dir: str = typer.Option(
        None,
        help="Nanopore fastq directory",
    ),
    ref_mmi: str = typer.Option(
        ...,
        help="Reference MMI (required)",
    ),
    ref_mmi_cache: str = typer.Option(
        PARAMS["ref_mmi_cache"],
        help="Cache directory for ref_mmi",
    ),
    min_cov: float = typer.Option(
        PARAMS["min_cov"],
        help="minimum coverage as a proportion of signature",
    ),
    min_reads: int = typer.Option(
        PARAMS["min_reads"],
        help="minimum number of reads mapped to be considered a hit",
    ),
    min_len: int = typer.Option(
        PARAMS["min_len"],
        help="minimum number of signature bases to be present for a strain to be considered present",
    ),
    max_z_score: int = typer.Option(
        PARAMS["max_Zscore"],
        help="maximum estimated z-score for the depth of the mapped region.",
    ),
    match_factor: float = typer.Option(
        PARAMS["match_factor"],
        help="0.5",
    ),
    gottcha2_cpus: int = typer.Option(
        PARAMS["gottcha2_cpus"],
        help="Number of CPUs for gottcha2",
    ),
    results: str = typer.Option(
        PARAMS["results"],
        help="Results directory",
    ),
    setup_results: str = typer.Option(
        PARAMS["setup_results"],
        help="Setup results directory",
    ),
    gottcha_results: str = typer.Option(
        PARAMS["gottcha_results"],
        help="Gottcha results directory",
    ),
    gottcha_sam: str = typer.Option(
        PARAMS["gottcha_sam"],
        help="Gottcha SAM files directory",
    ),
    gottcha_stats: str = typer.Option(
        PARAMS["gottcha_stats"],
        help="Gottcha stats TSVs directory",
    ),
    gottcha_fasta: str = typer.Option(
        PARAMS["gottcha_fasta"],
        help="Gottcha FASTA representative sequences directory",
    ),
) -> None:
    """
    Build and (optionally) execute a Nextflow run command using the chosen profile.

    The command is constructed as follows:

        nextflow run . -profile <profile> [-c <config>] [-p <params_file>]

    You can review the generated command and confirm whether to execute it.
    """  # Ensure that at least one of illumina_fastq_dir and nanopore_fastq_dir is provided.
    assert illumina_fastq_dir or nanopore_fastq_dir, (
        "Error: At least one of --illumina_fastq_dir or --nanopore_fastq_dir must be provided."
    )

    # Check each provided path.
    for arg_name, value in [
        ("config", config),
        ("params_file", params_file),
        ("illumina_fastq_dir", illumina_fastq_dir),
        ("nanopore_fastq_dir", nanopore_fastq_dir),
        ("ref_mmi", ref_mmi),
        ("ref_mmi_cache", ref_mmi_cache),
        ("min_cov", min_cov),
        ("min_reads", min_reads),
        ("min_len", min_len),
        ("max_Zscore", max_z_score),
        ("match_factor", match_factor),
        ("results", results),
        ("setup_results", setup_results),
        ("gottcha_results", gottcha_results),
        ("gottcha_sam", gottcha_sam),
        ("gottcha_stats", gottcha_stats),
        ("gottcha_fasta", gottcha_fasta),
    ]:
        if not value:
            continue
        check_path(value, arg_name)

    command = f"nextflow run . -profile {profile.value}"
    if config:
        command += f" -c {config}"
    if params_file:
        command += f" -p {params_file}"

    # Build a dictionary of parameters from user inputs.
    params_to_include = {
        "illumina_fastq_dir": illumina_fastq_dir,
        "nanopore_fastq_dir": nanopore_fastq_dir,
        "ref_mmi": ref_mmi,
        "gottcha2_cpus": gottcha2_cpus,
        "ref_mmi_cache": ref_mmi_cache,
        "min_cov": min_cov,
        "min_reads": min_reads,
        "min_len": min_len,
        "max_Zscore": max_z_score,
        "match_factor": match_factor,
        "results": results,
        "setup_results": setup_results,
        "gottcha_results": gottcha_results,
        "gottcha_sam": gottcha_sam,
        "gottcha_stats": gottcha_stats,
        "gottcha_fasta": gottcha_fasta,
    }

    # Append each parameter to the command.
    # For parameters with a default of null, include only if the user provided a value.
    for key, value in params_to_include.items():
        if PARAMS[key] is None and value is None:
            continue
        command += f" --{key} {value}"

    typer.echo("\nConstructed Nextflow command:")
    typer.echo(command)
    if typer.confirm("\nDo you want to execute this command?"):
        try:
            parsed_command = command.split(" ")
            subprocess.run(parsed_command, shell=False, check=True)  # noqa: S603
        except subprocess.CalledProcessError as e:
            typer.echo(f"Command failed with error:\n\n{e}")
    else:
        typer.echo("Command execution cancelled.")
