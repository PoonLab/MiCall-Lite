"""
Generate V3-specific nucleotide sequence from remapped env .seq file
Along with G2PFPR score in the header

Input: <sample>.<region>.remap.sam.<qCutoff>.fasta.<minCount>.seq
Output: <sample>.<region>.remap.sam.<qCutoff>.fasta.<minCount>.seq.V3
"""

# After remapping, dashes introduced into env sequence due to alignment
# Strip out dashes at this step

import os
import sys
from glob import glob
from Bio import SeqIO
from seqUtils import convert_fasta, translate_nuc
from hyphyAlign import HyPhy, change_settings, refSeqs, pair_align, get_boundaries, apply2nuc
from minG2P import conan_g2p

hyphy = HyPhy._THyPhy (os.getcwd(), 1)
change_settings(hyphy) 										# Default settings are for protein alignment
refseq = translate_nuc(refSeqs['V3, clinical'], 0)			# refSeq is V3 (HXB2: 7110-7217) in nucleotide space
proteinV3RefSeq = "CTRPNNNTRKSIHIGPGRAFYATGEIIGDIRQAHC"   	# Exactly the same as refseq (SO JUST TRANSLATE THE REFSEQ?)

helpOutput = """
Synopsis: Processes *.HIV1B-env.remap.sam.<qCutoff>.fasta.*.seq file into .V3 files (Works on all min count files)

Usage: python 4_extractV3_G2P_from_seqs_drop_censored_reads.py <qCutoff file to process> <folderContainingSeqFiles>
Ex: python 4_extractV3_G2P_from_seqs_drop_censored_reads.py 10 130524_M01841_0004_000000000-A43J1/Data/Intensities/BaseCalls/remap_sams/
"""

if len(sys.argv) != 3:
	print helpOutput
	sys.exit()

qCutoff = sys.argv[1]
globPath = sys.argv[2] + '*.HIV1B-env.remap.sam.' + qCutoff + '.fasta.*.seq'
files = glob(globPath)

# For each env-nucleotide unique fasta.seq fasta file
for f in files:

	infile = open(f, 'rU')
	try:
		fasta = convert_fasta(infile.readlines())
	except:
		print 'failed to convert', f
		continue
	infile.close()

	# Output file will contain V3 sequence and g2p data
	outfilename = f + ".v3"

	try:
		# Open file for writing - fail if file already exists
		fd = os.open(outfilename, os.O_WRONLY | os.O_CREAT | os.O_EXCL)
		outfile = os.fdopen(fd, "w")		# Convert to writable Python file object
		os.chmod(outfilename, 0644)			# Change permission to 644 (Leading 0 treated as octal)
	except:
		print "Already exists (SKIPPING): " + outfilename
		continue

	print "Writing to file: " + outfilename

	# Determine correct offset off the first sequence
	# to correct for frameshift induced by sample/region-specific remapping
	header1, envSeq1 = fasta[0]
	envSeq1 = envSeq1.strip("-")
	best_offset = -999
	best_score = -999
	for offset in range(3):								# range(3) = [0, 1, 2]
		aaEnvSeq = translate_nuc(envSeq1, offset)
		aquery, aref, ascore = pair_align(hyphy, proteinV3RefSeq, aaEnvSeq)

		if ascore > best_score:
			best_offset = offset
			best_score = ascore

		left, right = get_boundaries(aref)				# Get left/right boundaries of V3 protein
		v3prot = aquery[left:right]						# Extract V3 protein

	# For each env sequence, extract V3
	for header, envSeq in fasta:

		envSeq = envSeq.strip("-")						# Strip dashes at flanking regions generated by alignment
		aaEnvSeq = translate_nuc(envSeq, best_offset)	# Translate env on the correct offset (ORF)

		aquery, aref, ascore = pair_align(hyphy, proteinV3RefSeq, aaEnvSeq)
		left, right = get_boundaries(aref)									# Get left/right boundaries of V3 protein
		v3prot = aquery[left:right]											# Extract V3 protein
		g2p, fpr, aligned = conan_g2p(v3prot)								# And generate G2P score from it
		v3nuc = apply2nuc(envSeq[(3*left):], v3prot, aref[left:right], keepIns=True, keepDel=False)

		# Conditions for dropping data
		# 1) Censored bases were detected ('N')
		# 2) V3 didn't start with C, end with C
		# 3) V3 didn't contain an internal stop codon ('*')
		# 4) Alignment score less than 50

		if 'N' in v3nuc or not v3prot.startswith('C') or not v3prot.endswith('C') or '*' in v3prot or ascore < 50:
			pass
		else:
			header = header + '_G2PFPR_' + str(fpr)
			outfile.write(">" + header + "\n" + v3nuc + "\n")

	outfile.close()
