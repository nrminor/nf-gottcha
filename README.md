# 31230 nf-GOTTCHA prototype

Nextflow runner of gottcha2 for taxonomic classification of viruses in metagenomic sequence datasets.

## Overview

`nf-gottcha` is built as python command-liner interface, which itself runs Nextflow as an orchestrator, which itself then runs [`GOTTCHA2`](https://github.com/poeli/GOTTCHA2) with some helper tools. These tools include a setup process that downloads a required reference MMI database, or finds it in the local file system, as well as processes that upload the final taxonomic report data into the [DHO Lab Labkey System](https://dholk.primate.wisc.edu/project/home/begin.view?).

## Usage

Users can start exploring the interface with `nf-gotcha -h`. To explore controls over the workflow's execution, run `nf-gottcha run -h`, which will bring up a menu like this:

```
 Build and (optionally) execute a Nextflow run command using the chosen profile.
 The command is constructed as follows:
 nextflow run . -profile <profile> [-c <config>] [-p <params_file>]
 You can review the generated command and confirm whether to execute it.

╭─ Options ──────────────────────────────────────────────────────────────────────────────────────────╮
│    --profile             -r      [standard|docker|singularity|ap  Nextflow profile to use          │
│                                  ptainer|chtc_hpc|containerless]  (default: containerless)         │
│                                                                   [default: containerless]         │
│    --config              -c      TEXT                             Path to an additional Nextflow   │
│                                                                   configuration file               │
│    --params-file         -p      TEXT                             Path to an additional Nextflow   │
│                                                                   parameters file                  │
│    --illumina-fastq-dir          TEXT                             Illumina fastq directory         │
│                                                                   [default: None]                  │
│    --nanopore-fastq-dir          TEXT                             Nanopore fastq directory         │
│                                                                   [default: None]                  │
│ *  --ref-mmi                     TEXT                             Reference MMI (required)         │
│                                                                   [default: None]                  │
│                                                                   [required]                       │
│    --gottcha2-cpus               INTEGER                          Number of CPUs for gottcha2      │
│                                                                   [default: 8]                     │
│    --ref-mmi-cache               TEXT                             Cache directory for ref_mmi      │
│                                                                   [default:                        │
│                                                                   ${launchDir}/ref_mmi_cache]      │
│    --results                     TEXT                             Results directory                │
│                                                                   [default: ${launchDir}/results]  │
│    --setup-results               TEXT                             Setup results directory          │
│                                                                   [default: params.results +       │
│                                                                   '/00_setup']                     │
│    --gottcha-results             TEXT                             Gottcha results directory        │
│                                                                   [default: params.results +       │
│                                                                   '/01_gottcha2']                  │
│    --gottcha-sam                 TEXT                             Gottcha SAM files directory      │
│                                                                   [default: params.gottcha_results │
│                                                                   + '/01_sam_files']               │
│    --gottcha-stats               TEXT                             Gottcha stats TSVs directory     │
│                                                                   [default: params.gottcha_results │
│                                                                   + '/02_stats_tsvs']              │
│    --gottcha-fasta               TEXT                             Gottcha FASTA representative     │
│                                                                   sequences directory              │
│                                                                   [default: params.gottcha_results │
│                                                                   + '/03_representative_seqs']     │
│    --help                -h                                       Show this message and exit.      │
╰────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

## Setup

The `nf-gottcha` project, including dependencies, is declared in the repo's `pyproject.toml`. To install all dependencies, users should install the [`pixi` package manager](https://pixi.sh/latest/), run `pixi shell --frozen` in the terminal shell instance where you intend to run the workflow, and then use `nf-gottcha run` to run the pipeline with the desired settings.

