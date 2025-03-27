#!/usr/bin/env nextflow

// https://github.com/poeli/GOTTCHA2/wiki

workflow {

    assert params.ref_mmi : "A URI to a reference database in minimap2 MMI format must be provided with --ref_mmi. \
    This can be a URL or a local path."
    if !params.ref_mmi.startsWith("http") {
        assert file(params.ref_mmi).isFile() : "The file provided with ${params.ref_mmi} does not exist at that location."
    }

    ch_nanopore_fastqs = params.nanopore_fastq_dir ?
        Channel.fromPath("${nanopore_fastq_dir}/*.fastq.gz")
        .map( fastq -> tuple( file(fastq).getSimpleName(), fastq ) )
        : Channel.empty()

    ch_nanopore_fastqs = params.nanopore_fastq_dir ?
        Channel.fromFilePairs("${illumina_fastq_dir}*_R{1,2}.fastq", flat: false)
        : Channel.empty()

    ch_ref_uri = Channel.from(params.ref_mmi)


    SETUP(ch_ref_uri)

    GOTTCHA2(
        SETUP.out.mmi,
        ch_illumina_fastqs,
        ch_nanopore_fastqs
    )

    LABKEY(
        GOTTCHA.out.tsv,
        GOTTCHA.out.fasta
    )

}

workflow SETUP {

    take:
    ch_ref_uri

    main:
    DOWNLOAD_REF_DATASET(ch_ref_uri)

    emit:
    DOWNLOAD_REF_DATASET.out.mmi

}

workflow GOTTCHA2 {

    take:
    ch_ref_mmi
    ch_illumina_fastqs
    ch_nanopore_fastqs

    main:
    
    PROFILE_NANOPORE(
       ch_ref_mmi.combine(ch_fastq_files) 
    )

    PROFILE_ILLUMINA(
       ch_ref_mmi.combine(ch_fastq_files) 
    )

    GENERATE_FASTA(
        GOTTCHA2_NANOPORE.out.aligned.mix(GOTTCHA2_ILLUMINA.out.aligned)
    )

    emit:
    tsv = GOTTCHA2_NANOPORE.out.stats.filter(file -> file(file).getBaseName().endsWith("full.tsv"))
    fasta = GENERATE_FASTA.out

}

workflow LABKEY {

    take:
    ch_full_tsv
    ch_fasta

    main:
    SEND_TSV_TO_LABKEY(ch_full_tsv)

    SEND_FASTA_TO_LABKEY(ch_fasta)

}


process DOWNLOAD_REF_DATASET {
   
    storeDir params.ref_mmi_cache

    output:
    path mmi, emit: mmi

}

process PROFILE_NANOPORE {

    tag "${sample_id}"
    publishDir params.gottcha_sam, mode: 'copy', overwrite: false, pattern: "*.sam"
    publishDir params.gottcha_stats, mode: 'copy', overwrite: false, pattern: "*.tsv"

    cpus params.gottcha2_cpus
    // memory

    input:
    tuple path(ref_mmi), val(sample_id), path(fastq)

    output:
    path "${sample_id}*.sam", emit: aligned
    path "${sample_id}*.tsv", emit: stats

    script:
    String ref_prefix = file(ref_mmi).getBaseName().toString().replace(".mmi", "")
    """
    gottcha2.py  \
    --database ${ref_prefix} \
    --prefix ${sample_di} \
     -t ${task.cpus} \
    -i ${fastq} \
     --nanopore
    """

}

process PROFILE_ILLUMINA {

    tag "${sample_id}"
    publishDir params.gottcha_sam, mode: 'copy', overwrite: false, pattern: "*.sam"
    publishDir params.gottcha_stats, mode: 'copy', overwrite: false, pattern: "*.tsv"

    cpus params.gottcha2_cpus
    // memory

    input:
    tuple path(ref_mmi), val(sample_id), path(fastq1, path(fastq2))

    output:
    path "${sample_id}*.sam", emit: aligned
    path "${sample_id}*.tsv", emit: stats

    script:
    String ref_prefix = file(ref_mmi).getBaseName().toString().replace(".mmi", "")
    """
    gottcha2.py -d ${ref_prefix} -t ${task.cpus} -i ${fastq1} ${fastq2}
    """

}

process GENERATE_FASTA {

    tag "${sample_id}"
    publishDir params.gottcha_fasta, mode: 'copy', overwrite: false, pattern: "*.fasta"

    cpus params.gottcha2_cpus
    // memory

    input:
    tuple path(ref_mmi), val(sample_id), path(sam_files)

    output:
    path "*.fasta"

    script:
    String ref_prefix = file(ref_mmi).getBaseName().toString().replace(".mmi", "")
    """
    gottcha2.py \
    -s ${sample_id}.gottcha_species.sam \
    -ef \
    --nanopore \
    --database ${ref_mmi}
    """
    
}
