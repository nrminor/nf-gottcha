#!/usr/bin/env nextflow

// https://github.com/poeli/GOTTCHA2/wiki

workflow {

    ch_nanopore_fastqs = params.nanopore_fastq_dir
        ? Channel.fromPath("${params.nanopore_fastq_dir}/*.fastq.gz").map { fastq -> tuple(file(fastq).getSimpleName(), fastq) }
        : Channel.empty()

    ch_illumina_fastqs = params.illumina_fastq_dir
        ? Channel.fromFilePairs("${params.illumina_fastq_dir}*_R{1,2}.fastq", flat: false)
        : Channel.empty()

    ch_ref_files = Channel.fromPath("${params.ref_mmi}*")
        .collect(sort: true)
        .map { mmi, stats, tsv -> tuple( file(mmi), file(stats), file(tsv) ) }


    // SETUP(ch_ref_files)

    GOTTCHA2(
        ch_ref_files,
        ch_illumina_fastqs,
        ch_nanopore_fastqs,
    )
}

workflow SETUP {
    take:
    ch_ref_uri

    main:
    SETUP_REF_DATASET(ch_ref_uri)

    emit:
    mmi = SETUP_REF_DATASET.out.mmi
}

workflow GOTTCHA2 {
    take:
    ch_ref_files
    ch_illumina_fastqs
    ch_nanopore_fastqs

    main:

    PROFILE_NANOPORE(
        ch_ref_files.combine(ch_nanopore_fastqs)
    )

    PROFILE_ILLUMINA(
        ch_ref_files.combine(ch_illumina_fastqs)
    )

    GENERATE_FASTA(
        PROFILE_NANOPORE.out.aligned.mix(PROFILE_ILLUMINA.out.aligned)
    )

    emit:
    tsv   = PROFILE_NANOPORE.out.stats.filter { file -> file(file).getBaseName().endsWith("full.tsv") }
    fasta = GENERATE_FASTA.out
}

workflow LABKEY {
    take:
    ch_full_tsv
    ch_fasta

    main:
    SEND_TSV_TO_LABKEY(ch_full_tsv)
}


process SETUP_REF_DATASET {

    storeDir params.ref_mmi_cache

    errorStrategy 'ignore'

    input:
    path mmi

    output:
    path mmi, emit: mmi

    script:
    """
    validate_mmi.py ${mmi}
    """
}

process PROFILE_NANOPORE {

    tag "${sample_id}"
    publishDir params.gottcha_sam, mode: 'copy', overwrite: false, pattern: "*.sam"
    publishDir params.gottcha_stats, mode: 'copy', overwrite: false, pattern: "*.tsv"

    errorStrategy 'ignore'

    cpus params.gottcha2_cpus

    input:
    tuple path(ref_mmi), path(stats), path(tsv), val(sample_id), path(fastq)

    output:
    path "${sample_id}*.sam", emit: aligned
    path "${sample_id}*.tsv", emit: stats

    script:
    def String ref_prefix = file(ref_mmi).getBaseName().toString().replace(".mmi", "")
    """
    gottcha2.py  \
    --database ${ref_prefix} \
    --prefix ${sample_id} \
     -t ${task.cpus} \
    -i ${fastq} \
     --nanopore
    """
}

process PROFILE_ILLUMINA {

    tag "${sample_id}"
    publishDir params.gottcha_sam, mode: 'copy', overwrite: false, pattern: "*.sam"
    publishDir params.gottcha_stats, mode: 'copy', overwrite: false, pattern: "*.tsv"

    errorStrategy 'ignore'

    cpus params.gottcha2_cpus

    input:
    tuple path(ref_mmi), path(stats), path(tsv), val(sample_id), path(fastq1), path(fastq2)

    output:
    path "${sample_id}*.sam", emit: aligned
    path "${sample_id}*.tsv", emit: stats

    script:
    def String ref_prefix = file(ref_mmi).getBaseName().toString().replace(".mmi", "")
    """
    gottcha2.py -d ${ref_prefix} -t ${task.cpus} -i ${fastq1} ${fastq2}
    """
}

process GENERATE_FASTA {

    tag "${sample_id}"
    publishDir params.gottcha_fasta, mode: 'copy', overwrite: false, pattern: "*.fasta"

    errorStrategy 'ignore'

    cpus params.gottcha2_cpus

    input:
    tuple path(ref_mmi), val(sample_id), path(sam_files)

    output:
    path "*.fasta"

    script:
    def String ref_prefix = file(ref_mmi).getBaseName().toString().replace(".mmi", "")
    """
    gottcha2.py \
    -s ${sample_id}.gottcha_species.sam \
    -ef \
    --nanopore \
    --database ${ref_prefix}
    """
}

process SEND_TSV_TO_LABKEY {

    errorStrategy 'ignore'

    input:
    path tsv

    script:
    """
    push_tsv_to_labkey.py \
    ${tsv} \
    --labkey-url "https://<LABKEY-URL>.com" \
    --container "<LABKEY-FOLDER-PATH>" \
    --query-name "<QUERY-LIST-NAME>" \
    -v
    """
}
