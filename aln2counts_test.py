import StringIO
import unittest

import aln2counts
from testfixtures.logcapture import LogCapture

class SequenceReportTest(unittest.TestCase):
    def setUp(self):
        self.insertion_file = StringIO.StringIO()
        insert_writer = aln2counts.InsertionWriter(
            insert_file=self.insertion_file)
        seed_refs = {"R_NO_COORD": "ACTACTACT"} # Content ignored, just length
        coordinate_refs = {"R1": "KFR",
                           "R2": "KFGPR",
                           "R3": "KFQTPREH"}
        conseq_mixture_cutoffs = [0.1]
        self.report = aln2counts.SequenceReport(insert_writer,
                                                seed_refs,
                                                coordinate_refs,
                                                conseq_mixture_cutoffs)
        self.report_file = StringIO.StringIO()
     
    def testEmptyAminoReport(self):
        expected_text = ""
        aligned_reads = []
        
        self.report.read(aligned_reads)
        self.report.write_amino_counts(self.report_file)
         
        self.assertMultiLineEqual(expected_text, self.report_file.getvalue())
     
    def testConsensusFromSingleRead(self):
        """ In this sample, there is a single read with two codons.
        AAA -> K
        TTT -> F
        """
        #sample,refname,qcut,rank,count,offset,seq
        aligned_reads = """\
E1234_S1,R1,15,0,9,0,AAATTT
""".splitlines(True)
        expected_text = """\
sample,region,q-cutoff,s-number,consensus-percent-cutoff,sequence
E1234,R1,15,S1,MAX,AAATTT
E1234,R1,15,S1,0.100,AAATTT
"""
         
        self.report.write_consensus_header(self.report_file)
        self.report.read(aligned_reads)
        self.report.write_consensus(self.report_file)
         
        self.assertMultiLineEqual(expected_text, self.report_file.getvalue())
     
    def testConsensusFromTwoReads(self):
        """ The second read is out voted by the first one.
        CCC -> P
        GGG -> G
        """
        #sample,refname,qcut,rank,count,offset,seq
        aligned_reads = """\
E1234_S1,R1,15,0,9,0,AAATTT
E1234_S1,R1,15,0,1,0,CCCGGG
""".splitlines(True)
        expected_consensus = "KF"
         
        self.report.read(aligned_reads)
        consensus = self.report.consensus
         
        self.assertSequenceEqual(expected_consensus, consensus)
     
    def testSingleReadAminoReport(self):
        """ In this sample, there is a single read with two codons.
        AAA -> K
        TTT -> F
        The coordinate reference has three codons, so the third position is
        empty.
        """
        #sample,refname,qcut,rank,count,offset,seq
        aligned_reads = """\
E1234_S1,R1,15,0,9,0,AAATTT
""".splitlines(True)
         
        expected_text = """\
sample,region,q-cutoff,query.aa.pos,refseq.aa.pos,A,C,D,E,F,G,H,I,K,L,M,N,P,Q,R,S,T,V,W,Y,*
E1234_S1,R1,15,1,1,0,0,0,0,0,0,0,0,9,0,0,0,0,0,0,0,0,0,0,0,0
E1234_S1,R1,15,2,2,0,0,0,0,9,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
E1234_S1,R1,15,,3,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
"""        
        
        self.report.write_amino_header(self.report_file)
        self.report.read(aligned_reads)
        self.report.write_amino_counts(self.report_file)
        
        self.assertMultiLineEqual(expected_text, self.report_file.getvalue())
     
    def testSingleReadNucleotideReport(self):
        """ In this sample, there is a single read with two codons.
        AAA -> K
        TTT -> F
        The coordinate reference has three codons, so the third position is
        empty.
        """
        #sample,refname,qcut,rank,count,offset,seq
        aligned_reads = """\
E1234_S1,R1,15,0,9,0,AAATTT
""".splitlines(True)
          
        #sample,region,q-cutoff,query.nuc.pos,refseq.nuc.pos,A,C,G,T
        expected_text = """\
sample,region,q-cutoff,query.nuc.pos,refseq.nuc.pos,A,C,G,T
E1234_S1,R1,15,1,1,9,0,0,0
E1234_S1,R1,15,2,2,9,0,0,0
E1234_S1,R1,15,3,3,9,0,0,0
E1234_S1,R1,15,4,4,0,0,0,9
E1234_S1,R1,15,5,5,0,0,0,9
E1234_S1,R1,15,6,6,0,0,0,9
E1234_S1,R1,15,,7,0,0,0,0
E1234_S1,R1,15,,8,0,0,0,0
E1234_S1,R1,15,,9,0,0,0,0
"""
        
        self.report.write_nuc_header(self.report_file)
        self.report.read(aligned_reads)
        self.report.write_nuc_counts(self.report_file)
        
        self.assertMultiLineEqual(expected_text, self.report_file.getvalue())
     
    def testOffsetNucleotideReport(self):
        """ The first row provides alignment so the partial codon at the start
        of the second row will map to the reference.
        """
        #sample,refname,qcut,rank,count,offset,seq
        aligned_reads = """\
E1234_S1,R1,15,0,1,3,TTT
E1234_S1,R1,15,0,8,5,TCGA
""".splitlines(True)
          
        #sample,region,q-cutoff,query.nuc.pos,refseq.nuc.pos,A,C,G,T
        expected_text = """\
E1234_S1,R1,15,1,1,0,0,0,0
E1234_S1,R1,15,2,2,0,0,0,0
E1234_S1,R1,15,3,3,0,0,0,0
E1234_S1,R1,15,4,4,0,0,0,1
E1234_S1,R1,15,5,5,0,0,0,1
E1234_S1,R1,15,6,6,0,0,0,9
E1234_S1,R1,15,7,7,0,8,0,0
E1234_S1,R1,15,8,8,0,0,8,0
E1234_S1,R1,15,9,9,8,0,0,0
"""
        
        self.report.read(aligned_reads)
        self.report.write_nuc_counts(self.report_file)
        
        self.assertMultiLineEqual(expected_text, self.report_file.getvalue())
    
    def testPartialCodonNucleotideReport(self):
        #sample,refname,qcut,rank,count,offset,seq
        aligned_reads = """\
E1234_S1,R1,15,0,9,0,AAATT
""".splitlines(True)
        
        #sample,region,q-cutoff,query.nuc.pos,refseq.nuc.pos,A,C,G,T
        expected_text = """\
E1234_S1,R1,15,1,1,9,0,0,0
E1234_S1,R1,15,2,2,9,0,0,0
E1234_S1,R1,15,3,3,9,0,0,0
E1234_S1,R1,15,4,4,0,0,0,9
E1234_S1,R1,15,5,5,0,0,0,9
E1234_S1,R1,15,6,6,0,0,0,0
E1234_S1,R1,15,,7,0,0,0,0
E1234_S1,R1,15,,8,0,0,0,0
E1234_S1,R1,15,,9,0,0,0,0
"""
          
        self.report.read(aligned_reads)
        self.report.write_nuc_counts(self.report_file)
         
        self.assertMultiLineEqual(expected_text, self.report_file.getvalue())
    
    def testDeletionBetweenSeedAndCoordinateNucleotideReport(self):
        """ Coordinate sequence is KFGPR, and this aligned read is KFPR.
         
        Must be a deletion in the seed reference with respect to the coordinate
        reference.
        """
        #sample,refname,qcut,rank,count,offset,seq
        aligned_reads = """\
E1234_S1,R2,15,0,9,0,AAATTTCCCCGA
""".splitlines(True)
           
        #sample,region,q-cutoff,query.nuc.pos,refseq.nuc.pos,A,C,G,T
        expected_text = """\
E1234_S1,R2,15,1,1,9,0,0,0
E1234_S1,R2,15,2,2,9,0,0,0
E1234_S1,R2,15,3,3,9,0,0,0
E1234_S1,R2,15,4,4,0,0,0,9
E1234_S1,R2,15,5,5,0,0,0,9
E1234_S1,R2,15,6,6,0,0,0,9
E1234_S1,R2,15,,7,0,0,0,0
E1234_S1,R2,15,,8,0,0,0,0
E1234_S1,R2,15,,9,0,0,0,0
E1234_S1,R2,15,7,10,0,9,0,0
E1234_S1,R2,15,8,11,0,9,0,0
E1234_S1,R2,15,9,12,0,9,0,0
E1234_S1,R2,15,10,13,0,9,0,0
E1234_S1,R2,15,11,14,0,0,9,0
E1234_S1,R2,15,12,15,9,0,0,0
"""
           
        self.report.read(aligned_reads)
        self.report.write_nuc_counts(self.report_file)
        
        self.assertMultiLineEqual(expected_text, self.report_file.getvalue())
    
    def testDeletionBetweenSeedAndCoordinateAminoReport(self):
        """ Coordinate sequence is KFGPR, and this aligned read is KFPR.
         
        Must be a deletion in the seed reference with respect to the coordinate
        reference.
        """
        #sample,refname,qcut,rank,count,offset,seq
        aligned_reads = """\
E1234_S1,R2,15,0,9,0,AAATTTCCCCGA
""".splitlines(True)
           
        #sample,region,q-cutoff,query.aa.pos,refseq.aa.pos,
        #          A,C,D,E,F,G,H,I,K,L,M,N,P,Q,R,S,T,V,W,Y,*
        expected_text = """\
E1234_S1,R2,15,1,1,0,0,0,0,0,0,0,0,9,0,0,0,0,0,0,0,0,0,0,0,0
E1234_S1,R2,15,2,2,0,0,0,0,9,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
E1234_S1,R2,15,,3,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
E1234_S1,R2,15,3,4,0,0,0,0,0,0,0,0,0,0,0,0,9,0,0,0,0,0,0,0,0
E1234_S1,R2,15,4,5,0,0,0,0,0,0,0,0,0,0,0,0,0,0,9,0,0,0,0,0,0
"""
        
        self.report.read(aligned_reads)
        self.report.write_amino_counts(self.report_file)
        
        self.assertMultiLineEqual(expected_text, self.report_file.getvalue())
    
    def testDeletionWithMinorityVariant(self):
        """ Aligned reads are mostly K-R, but some are KFR.
        
        Must be a deletion in the sample with respect to the seed reference,
        but some variants in the sample do not have that deletion.
        """
        #sample,refname,qcut,rank,count,offset,seq
        aligned_reads = """\
E1234_S1,R1,15,0,5,0,AAA---CGA
E1234_S1,R1,15,0,2,0,AAATTTCGA
""".splitlines(True)
           
        #sample,region,q-cutoff,query.aa.pos,refseq.aa.pos,
        #          A,C,D,E,F,G,H,I,K,L,M,N,P,Q,R,S,T,V,W,Y,*
        expected_text = """\
E1234_S1,R1,15,1,1,0,0,0,0,0,0,0,0,7,0,0,0,0,0,0,0,0,0,0,0,0
E1234_S1,R1,15,2,2,0,0,0,0,2,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
E1234_S1,R1,15,3,3,0,0,0,0,0,0,0,0,0,0,0,0,0,0,7,0,0,0,0,0,0
"""
        
        self.report.read(aligned_reads)
        self.report.write_amino_counts(self.report_file)
        
        self.assertMultiLineEqual(expected_text, self.report_file.getvalue())
    
    def testInsertionBetweenSeedAndCoordinateAminoReport(self):
        """ Coordinate sequence is KFQTPREH, and this aligned read is KFQTGPREH.
         
        The G must be an insertion in the seed reference with respect to the
        coordinate reference.
        """
        #sample,refname,qcut,rank,count,offset,seq
        aligned_reads = """\
E1234_S1,R3,15,0,9,0,AAATTTCAGACTGGGCCCCGAGAGCAT
""".splitlines(True)
           
        #sample,region,q-cutoff,query.aa.pos,refseq.aa.pos,
        #          A,C,D,E,F,G,H,I,K,L,M,N,P,Q,R,S,T,V,W,Y,*
        expected_text = """\
E1234_S1,R3,15,1,1,0,0,0,0,0,0,0,0,9,0,0,0,0,0,0,0,0,0,0,0,0
E1234_S1,R3,15,2,2,0,0,0,0,9,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
E1234_S1,R3,15,3,3,0,0,0,0,0,0,0,0,0,0,0,0,0,9,0,0,0,0,0,0,0
E1234_S1,R3,15,4,4,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,9,0,0,0,0
E1234_S1,R3,15,6,5,0,0,0,0,0,0,0,0,0,0,0,0,9,0,0,0,0,0,0,0,0
E1234_S1,R3,15,7,6,0,0,0,0,0,0,0,0,0,0,0,0,0,0,9,0,0,0,0,0,0
E1234_S1,R3,15,8,7,0,0,0,9,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
E1234_S1,R3,15,9,8,0,0,0,0,0,0,9,0,0,0,0,0,0,0,0,0,0,0,0,0,0
"""
        expected_insertions = """\
sample,region,qcut,left,insert,count
E1234_S1,R3,15,5,G,9
"""

        self.report.read(aligned_reads)
        self.report.write_amino_counts(self.report_file)
        self.report.write_insertions()
        
        self.assertMultiLineEqual(expected_text, self.report_file.getvalue())
        self.assertMultiLineEqual(expected_insertions,
                                  self.insertion_file.getvalue())
    
    def testGapBetweenForwardAndReverse(self):
        """ Lower-case n represents a gap between forward and reverse reads.
        
        Region R2 has sequence KFGPR, so this read has a gap at the end of G
        and beginning of P. G is still unambiguous, but P is not.
        """
        #sample,refname,qcut,rank,count,offset,seq
        aligned_reads = """\
E1234_S1,R2,15,0,5,0,AAATTTGGnnCCCGA
""".splitlines(True)
           
        #sample,region,q-cutoff,query.aa.pos,refseq.aa.pos,
        #          A,C,D,E,F,G,H,I,K,L,M,N,P,Q,R,S,T,V,W,Y,*
        expected_text = """\
E1234_S1,R2,15,1,1,0,0,0,0,0,0,0,0,5,0,0,0,0,0,0,0,0,0,0,0,0
E1234_S1,R2,15,2,2,0,0,0,0,5,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
E1234_S1,R2,15,3,3,0,0,0,0,0,5,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
E1234_S1,R2,15,4,4,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
E1234_S1,R2,15,5,5,0,0,0,0,0,0,0,0,0,0,0,0,0,0,5,0,0,0,0,0,0
"""
        
        self.report.read(aligned_reads)
        self.report.write_amino_counts(self.report_file)
        
        self.assertMultiLineEqual(expected_text, self.report_file.getvalue())
    
    def testFailedAlignmentAminoReport(self):
        #sample,refname,qcut,rank,count,offset,seq
        aligned_reads = """\
E1234_S1,R1,15,0,2,0,TTATCCTAC
""".splitlines(True)
           
        expected_text = ""
        
        self.report.read(aligned_reads)
        self.report.write_amino_counts(self.report_file)
        
        self.assertMultiLineEqual(expected_text, self.report_file.getvalue())
    
    def testFailedAlignmentFailureReport(self):
        #sample,refname,qcut,rank,count,offset,seq
        aligned_reads = """\
E1234_S1,R1,15,0,2,0,TTATCCTAC
""".splitlines(True)
        
        expected_text = """\
sample,region,qcut,queryseq,refseq
E1234_S1,R1,15,LSY,KFR
"""
        
        self.report.write_failure_header(self.report_file)
        self.report.read(aligned_reads)
        self.report.write_failure(self.report_file)
        
        self.assertMultiLineEqual(expected_text, self.report_file.getvalue())
       
    def testNoFailureReport(self):
        #sample,refname,qcut,rank,count,offset,seq
        aligned_reads = """\
E1234_S1,R1,15,0,9,0,AAATTT
""".splitlines(True)
         
        expected_text = ""
        
        self.report.read(aligned_reads)
        self.report.write_failure(self.report_file)
        
        self.assertMultiLineEqual(expected_text, self.report_file.getvalue())
     
    def testRegionWithoutCoordinateReferenceNucleotideReport(self):
        #sample,refname,qcut,rank,count,offset,seq
        aligned_reads = """\
E1234_S1,R_NO_COORD,15,0,9,0,AAATTT
""".splitlines(True)
          
        #sample,region,q-cutoff,query.nuc.pos,refseq.nuc.pos,A,C,G,T
        expected_text = """\
E1234_S1,R_NO_COORD,15,1,,9,0,0,0
E1234_S1,R_NO_COORD,15,2,,9,0,0,0
E1234_S1,R_NO_COORD,15,3,,9,0,0,0
E1234_S1,R_NO_COORD,15,4,,0,0,0,9
E1234_S1,R_NO_COORD,15,5,,0,0,0,9
E1234_S1,R_NO_COORD,15,6,,0,0,0,9
E1234_S1,R_NO_COORD,15,7,,0,0,0,0
E1234_S1,R_NO_COORD,15,8,,0,0,0,0
E1234_S1,R_NO_COORD,15,9,,0,0,0,0
"""
        
        self.report.read(aligned_reads)
        self.report.write_nuc_counts(self.report_file)
        
        self.assertMultiLineEqual(expected_text, self.report_file.getvalue())
     
    def testRegionWithoutCoordinateReferenceFailureReport(self):
        #sample,refname,qcut,rank,count,offset,seq
        aligned_reads = """\
E1234_S1,R_NO_COORD,15,0,9,0,AAATTT
""".splitlines(True)
          
        expected_text = ""
        
        self.report.read(aligned_reads)
        self.report.write_failure(self.report_file)
        
        self.assertMultiLineEqual(expected_text, self.report_file.getvalue())
     
class AminoFrequencyWriterTest(unittest.TestCase):
    def setUp(self):
        self.writer = aln2counts.AminoFrequencyWriter(aafile=StringIO.StringIO(),
                                                      refseqs = {'R1': 'XXX',
                                                                 'R2': 'YYYY'})
        
    def testUnmappedRegion(self):
        expected_text = """\
sample,region,q-cutoff,query.aa.pos,refseq.aa.pos,A,C,D,E,F,G,H,I,K,L,M,N,P,Q,R,S,T,V,W,Y,*
"""
        
        self.writer.write(sample_name = 'E1234_S1',
                          region='R1',
                          qcut=15,
                          qindex_to_refcoord={},
                          amino_counts={},
                          inserts=[])
        
        self.assertMultiLineEqual(expected_text, self.writer.aafile.getvalue())
        
    def testWriteAminosFullRegion(self):
        expected_text = """\
sample,region,q-cutoff,query.aa.pos,refseq.aa.pos,A,C,D,E,F,G,H,I,K,L,M,N,P,Q,R,S,T,V,W,Y,*
E1234_S1,R1,15,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0
E1234_S1,R1,15,1,2,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0
E1234_S1,R1,15,2,3,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0
"""
        
        self.writer.write(sample_name = 'E1234_S1',
                          region='R1',
                          qcut=15,
                          qindex_to_refcoord={0:0, 1:1, 2:2},
                          amino_counts={0: {'Q': 1}, 1: {'R': 1}, 2: {'S': 1}},
                          inserts=[])
        
        self.assertMultiLineEqual(expected_text, self.writer.aafile.getvalue())
        
    def testWriteAminosEndOfRegion(self):
        expected_text = """\
sample,region,q-cutoff,query.aa.pos,refseq.aa.pos,A,C,D,E,F,G,H,I,K,L,M,N,P,Q,R,S,T,V,W,Y,*
E1234_S1,R1,15,,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
E1234_S1,R1,15,1,2,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0
E1234_S1,R1,15,2,3,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0
"""

        self.writer.write(sample_name = 'E1234_S1',
                          region='R1',
                          qcut=15,
                          qindex_to_refcoord={0:1, 1:2},
                          amino_counts={1: {'R': 1}, 2: {'S': 1}},
                          inserts=[])
        
        self.assertMultiLineEqual(expected_text, self.writer.aafile.getvalue())
        
    def testWriteAminosStartOfRegion(self):
        expected_text = """\
sample,region,q-cutoff,query.aa.pos,refseq.aa.pos,A,C,D,E,F,G,H,I,K,L,M,N,P,Q,R,S,T,V,W,Y,*
E1234_S1,R1,15,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0
E1234_S1,R1,15,1,2,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0
E1234_S1,R1,15,,3,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
"""

        self.writer.write(sample_name = 'E1234_S1',
                          region='R1',
                          qcut=15,
                          qindex_to_refcoord={0:0, 1:1},
                          amino_counts={0: {'Q': 1}, 1: {'R': 1}},
                          inserts=[])
        
        self.assertMultiLineEqual(expected_text, self.writer.aafile.getvalue())
        
    def testWriteAminosWithInsert(self):
        expected_text = """\
sample,region,q-cutoff,query.aa.pos,refseq.aa.pos,A,C,D,E,F,G,H,I,K,L,M,N,P,Q,R,S,T,V,W,Y,*
E1234_S1,R1,15,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0
E1234_S1,R1,15,2,2,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0
E1234_S1,R1,15,3,3,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0
"""

        self.writer.write(sample_name = 'E1234_S1',
                          region='R1',
                          qcut=15,
                          qindex_to_refcoord={0:0, 2:1, 3:2},
                          amino_counts={0: {'Q': 1},
                                        1: {'F': 1}, # This is the insert
                                        2: {'R': 1},
                                        3: {'S': 1}},
                          inserts=[1])
        
        self.assertMultiLineEqual(expected_text, self.writer.aafile.getvalue())
        
    def testWriteAminosWithDeletion(self):
        expected_text = """\
sample,region,q-cutoff,query.aa.pos,refseq.aa.pos,A,C,D,E,F,G,H,I,K,L,M,N,P,Q,R,S,T,V,W,Y,*
E1234_S1,R1,15,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0
E1234_S1,R1,15,,2,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
E1234_S1,R1,15,1,3,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0
"""

        self.writer.write(sample_name = 'E1234_S1',
                          region='R1',
                          qcut=15,
                          qindex_to_refcoord={0:0, 1:2},
                          amino_counts={0: {'Q': 1}, 1: {'S': 1}},
                          inserts=[])
        
        self.assertMultiLineEqual(expected_text, self.writer.aafile.getvalue())
        
    def testWriteAminosWithGap(self):
        expected_text = """\
sample,region,q-cutoff,query.aa.pos,refseq.aa.pos,A,C,D,E,F,G,H,I,K,L,M,N,P,Q,R,S,T,V,W,Y,*
E1234_S1,R1,15,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0
E1234_S1,R1,15,,2,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
E1234_S1,R1,15,2,3,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0
"""
        
        self.writer.write(sample_name = 'E1234_S1',
                          region='R1',
                          qcut=15,
                          qindex_to_refcoord={0:0, 2:2},
                          amino_counts={0: {'Q': 1}, 2: {'S': 1}},
                          inserts=[])
        
        self.assertMultiLineEqual(expected_text, self.writer.aafile.getvalue())

        
    def testWriteAminosTwoRegions(self):
        expected_text = """\
sample,region,q-cutoff,query.aa.pos,refseq.aa.pos,A,C,D,E,F,G,H,I,K,L,M,N,P,Q,R,S,T,V,W,Y,*
E1234_S1,R1,15,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0
E1234_S1,R1,15,1,2,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0
E1234_S1,R1,15,2,3,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0
E1234_S1,R2,15,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0
E1234_S1,R2,15,1,2,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0
E1234_S1,R2,15,2,3,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0
E1234_S1,R2,15,3,4,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0
"""
        
        self.writer.write(sample_name = 'E1234_S1',
                          region='R1',
                          qcut=15,
                          qindex_to_refcoord={0:0, 1:1, 2:2},
                          amino_counts={0: {'Q': 1}, 1: {'R': 1}, 2: {'S': 1}},
                          inserts=[])
        self.writer.write(sample_name = 'E1234_S1',
                          region='R2',
                          qcut=15,
                          qindex_to_refcoord={0:0, 1:1, 2:2, 3:3},
                          amino_counts={0: {'T': 1}, 1: {'S': 1}, 2: {'R': 1}, 3: {'Q': 1}},
                          inserts=[])
        
        self.assertMultiLineEqual(expected_text, self.writer.aafile.getvalue())

class NucleotideFrequencyWriterTest(unittest.TestCase):
    def setUp(self):
        self.writer = aln2counts.NucleotideFrequencyWriter(
            nucfile=StringIO.StringIO(),
            amino_ref_seqs = {'R1': 'EE', # contents irrelevant, length matters
                              'R2': 'EEE'},
            nuc_ref_seqs = {'R3': 'AAA',
                            'R4': 'AAAAAAAAA'}) # contents irrelevant, length matters
        
    def testNoWrites(self):
        expected_text = """\
sample,region,q-cutoff,query.nuc.pos,refseq.nuc.pos,A,C,G,T
"""
        
        self.assertMultiLineEqual(expected_text, self.writer.nucfile.getvalue())
        
    def testWithoutReference(self):
        # A region with no amino reference, like HLA.
        expected_text = """\
sample,region,q-cutoff,query.nuc.pos,refseq.nuc.pos,A,C,G,T
E1234_S1,R3,15,1,,1,2,0,0
E1234_S1,R3,15,2,,0,0,0,3
E1234_S1,R3,15,3,,0,0,0,0
"""
        
        self.writer.write(sample_name = 'E1234_S1',
                          region='R3',
                          qcut=15,
                          nuc_counts={0: {'A': 1, 'C': 2},
                                      1: {'T': 3}})
        
        self.assertMultiLineEqual(expected_text, self.writer.nucfile.getvalue())
        
    def testWithReference(self):
        expected_text = """\
sample,region,q-cutoff,query.nuc.pos,refseq.nuc.pos,A,C,G,T
E1234_S1,R1,15,1,1,1,2,0,0
E1234_S1,R1,15,2,2,0,0,0,3
E1234_S1,R1,15,,3,0,0,0,0
E1234_S1,R1,15,,4,0,0,0,0
E1234_S1,R1,15,,5,0,0,0,0
E1234_S1,R1,15,,6,0,0,0,0
"""
        
        self.writer.write(sample_name = 'E1234_S1',
                          region='R1',
                          qcut=15,
                          nuc_counts={0: {'A': 1, 'C': 2},
                                      1: {'T': 3}},
                          qindex_to_refcoord={0: 0},
                          min_offset=0)
        
        self.assertMultiLineEqual(expected_text, self.writer.nucfile.getvalue())
        
    def testOffsetWithoutReference(self):
        # A region with no amino reference, like HLA.
        expected_text = """\
sample,region,q-cutoff,query.nuc.pos,refseq.nuc.pos,A,C,G,T
E1234_S1,R4,15,1,,0,0,0,0
E1234_S1,R4,15,2,,0,0,0,0
E1234_S1,R4,15,3,,0,0,0,0
E1234_S1,R4,15,4,,0,0,0,0
E1234_S1,R4,15,5,,0,0,0,0
E1234_S1,R4,15,6,,1,2,0,0
E1234_S1,R4,15,7,,0,0,0,3
E1234_S1,R4,15,8,,0,0,0,0
E1234_S1,R4,15,9,,0,0,0,0
"""
        
        self.writer.write(sample_name = 'E1234_S1',
                          region='R4',
                          qcut=15,
                          nuc_counts={5: {'A': 1, 'C': 2},
                                      6: {'T': 3}})
        
        self.assertMultiLineEqual(expected_text, self.writer.nucfile.getvalue())
        
    def testOffsetWithReference(self):
        # No coverage at the start of the reference, and first codon starts
        # with its second nucleotide. The partial codon is output.
        expected_text = """\
sample,region,q-cutoff,query.nuc.pos,refseq.nuc.pos,A,C,G,T
E1234_S1,R2,15,,1,0,0,0,0
E1234_S1,R2,15,,2,0,0,0,0
E1234_S1,R2,15,,3,0,0,0,0
E1234_S1,R2,15,,4,0,0,0,0
E1234_S1,R2,15,,5,0,0,0,0
E1234_S1,R2,15,,6,0,0,0,0
E1234_S1,R2,15,7,7,0,0,1,0
E1234_S1,R2,15,8,8,0,0,1,0
E1234_S1,R2,15,9,9,1,0,0,0
"""
        
        with LogCapture() as log:
            self.writer.write(sample_name = 'E1234_S1',
                              region='R2',
                              qcut=15,
                              nuc_counts={4: {'T': 1},
                                          5: {'G': 1},
                                          6: {'G': 1},
                                          7: {'G': 1},
                                          8: {'A': 1}},
                              qindex_to_refcoord={1: 2},
                              min_offset=4)
        
        self.assertMultiLineEqual(expected_text, self.writer.nucfile.getvalue())
        log.check(('root',
                   'WARNING',
                   "No coordinate mapping for query nuc 4 (amino 0) in E1234_S1"),
                  ('root',
                   'WARNING',
                   "No coordinate mapping for query nuc 5 (amino 0) in E1234_S1"))
        
    def testGapWithoutReference(self):
        expected_text = """\
sample,region,q-cutoff,query.nuc.pos,refseq.nuc.pos,A,C,G,T
E1234_S1,R4,15,1,,1,2,0,0
E1234_S1,R4,15,2,,0,0,0,3
E1234_S1,R4,15,3,,0,0,0,0
E1234_S1,R4,15,4,,0,0,3,0
E1234_S1,R4,15,5,,0,0,0,0
E1234_S1,R4,15,6,,0,0,0,0
E1234_S1,R4,15,7,,0,0,0,0
E1234_S1,R4,15,8,,0,0,0,0
E1234_S1,R4,15,9,,0,0,0,0
"""
        
        self.writer.write(sample_name = 'E1234_S1',
                          region='R4',
                          qcut=15,
                          nuc_counts={0: {'A': 1, 'C': 2},
                                      1: {'T': 3},
                                      3: {'G': 3}})
        
        self.assertMultiLineEqual(expected_text, self.writer.nucfile.getvalue())
        
    def testGapWithReference(self):
        expected_text = """\
sample,region,q-cutoff,query.nuc.pos,refseq.nuc.pos,A,C,G,T
E1234_S1,R1,15,1,1,1,2,0,0
E1234_S1,R1,15,2,2,0,0,0,3
E1234_S1,R1,15,,3,0,0,0,0
E1234_S1,R1,15,4,4,0,0,3,0
E1234_S1,R1,15,,5,0,0,0,0
E1234_S1,R1,15,,6,0,0,0,0
"""
        
        self.writer.write(sample_name = 'E1234_S1',
                          region='R1',
                          qcut=15,
                          nuc_counts={0: {'A': 1, 'C': 2},
                                      1: {'T': 3},
                                      3: {'G': 3}},
                          qindex_to_refcoord={0: 0, 1: 1},
                          min_offset=0)
        
        self.assertMultiLineEqual(expected_text, self.writer.nucfile.getvalue())
        
    def testInsertionWithReference(self):
        expected_text = """\
sample,region,q-cutoff,query.nuc.pos,refseq.nuc.pos,A,C,G,T
E1234_S1,R2,15,1,1,1,2,0,0
E1234_S1,R2,15,2,2,0,0,0,3
E1234_S1,R2,15,3,3,0,2,0,0
E1234_S1,R2,15,,4,0,0,0,0
E1234_S1,R2,15,,5,0,0,0,0
E1234_S1,R2,15,,6,0,0,0,0
E1234_S1,R2,15,4,7,0,0,3,0
E1234_S1,R2,15,,8,0,0,0,0
E1234_S1,R2,15,,9,0,0,0,0
"""
        
        self.writer.write(sample_name = 'E1234_S1',
                          region='R2',
                          qcut=15,
                          nuc_counts={0: {'A': 1, 'C': 2},
                                      1: {'T': 3},
                                      2: {'C': 2},
                                      3: {'G': 3}},
                          qindex_to_refcoord={0: 0, 1: 2},
                          min_offset=0)
        
        self.assertMultiLineEqual(expected_text, self.writer.nucfile.getvalue())

class CoordinateMapTest(unittest.TestCase):
    def testStraightMapping(self):
        query_sequence =     'CTRPNNN'
        reference_sequence = 'CTRPNNN'
        expected_inserts = []
        expected_mapping = {0:0, 1:1, 2:2, 3:3, 4:4, 5:5, 6:6}
        
        qindex_to_refcoord, inserts = aln2counts.coordinate_map(
            query_sequence,
            reference_sequence)
        
        self.assertEqual(qindex_to_refcoord, expected_mapping)
        self.assertEqual(inserts, expected_inserts)
        
    def testInsertion(self):
        query_sequence =     'CTNPRPNNN'
        reference_sequence = 'CT--RPNNN'
        expected_inserts = [2, 3]
        expected_mapping = {0:0, 1:1, 4:2, 5:3, 6:4, 7:5, 8:6}
        
        qindex_to_refcoord, inserts = aln2counts.coordinate_map(
            query_sequence,
            reference_sequence)
        
        self.assertEqual(expected_mapping, qindex_to_refcoord)
        self.assertEqual(expected_inserts, inserts)
        
    def testDeletion(self):
        query_sequence =     'CT--NNN'
        reference_sequence = 'CTRPNNN'
        expected_inserts = []
        expected_mapping = {0:0, 1:1, 2:4, 3:5, 4:6}
        
        qindex_to_refcoord, inserts = aln2counts.coordinate_map(
            query_sequence,
            reference_sequence)
        
        self.assertEqual(expected_mapping, qindex_to_refcoord)
        self.assertEqual(expected_inserts, inserts)
        
    def testDeletionAndInsertion(self):
        query_sequence =     'CT--NNCPN'
        reference_sequence = 'CTRPNN--N'
        expected_inserts = [4, 5] # note that these are the non-blank indexes
        expected_mapping = {0:0, 1:1, 2:4, 3:5, 6:6}
        
        qindex_to_refcoord, inserts = aln2counts.coordinate_map(
            query_sequence,
            reference_sequence)
        
        self.assertEqual(qindex_to_refcoord, expected_mapping)
        self.assertEqual(inserts, expected_inserts)
        
    def testQueryStartsBeforeReference(self):
        query_sequence =     'NPCTRPNNN'
        reference_sequence = '--CTRPNNN'
        expected_inserts = []
        expected_mapping = {2:0, 3:1, 4:2, 5:3, 6:4, 7:5, 8:6}
        
        qindex_to_refcoord, inserts = aln2counts.coordinate_map(
            query_sequence,
            reference_sequence)
        
        self.assertEqual(expected_mapping, qindex_to_refcoord)
        self.assertEqual(expected_inserts, inserts)
        
    def testQueryEndsAfterReference(self):
        query_sequence =     'CTRPNNNNP'
        reference_sequence = 'CTRPNNN--'
        expected_inserts = []
        expected_mapping = {0:0, 1:1, 2:2, 3:3, 4:4, 5:5, 6:6}
        
        qindex_to_refcoord, inserts = aln2counts.coordinate_map(
            query_sequence,
            reference_sequence)
        
        self.assertEqual(expected_mapping, qindex_to_refcoord)
        self.assertEqual(expected_inserts, inserts)
        
    def testAmbiguous(self):
        query_sequence =     'CT?PNNN'
        reference_sequence = 'CTRPNNN'
        expected_inserts = []
        expected_mapping = {0:0, 1:1, 3:3, 4:4, 5:5, 6:6}
        
        qindex_to_refcoord, inserts = aln2counts.coordinate_map(
            query_sequence,
            reference_sequence)
        
        self.assertEqual(qindex_to_refcoord, expected_mapping)
        self.assertEqual(inserts, expected_inserts)

class InsertionWriterTest(unittest.TestCase):
    def setUp(self):
        self.writer = aln2counts.InsertionWriter(insert_file=StringIO.StringIO())
        self.writer.start_group(sample_name='E1234_S1', region='R1', qcut=15)
        
    def testNoInserts(self):
        expected_text = """\
sample,region,qcut,left,insert,count
"""
        
        self.writer.add_read(offset_sequence='ACDEF', count=1)
        self.writer.write(inserts=[])
        
        self.assertEqual(expected_text, self.writer.insert_file.getvalue())
        
    def testInsert(self):
        expected_text = """\
sample,region,qcut,left,insert,count
E1234_S1,R1,15,3,D,1
"""
        
        self.writer.add_read(offset_sequence='ACDEF', count=1)
        self.writer.write(inserts=[2])
        
        self.assertMultiLineEqual(expected_text, self.writer.insert_file.getvalue())
        
    def testInsertWithOffset(self):
        expected_text = """\
sample,region,qcut,left,insert,count
E1234_S1,R1,15,3,D,1
"""
        
        self.writer.add_read(offset_sequence='-CDEFG', count=1)
        self.writer.write(inserts=[2])
        
        self.assertMultiLineEqual(expected_text, self.writer.insert_file.getvalue())
        
    def testTwoInsertsWithOffset(self):
        expected_text = """\
sample,region,qcut,left,insert,count
E1234_S1,R1,15,3,D,1
E1234_S1,R1,15,5,F,1
"""
        
        self.writer.add_read(offset_sequence='-CDEFG', count=1)
        self.writer.write(inserts=[2, 4])
        
        self.assertMultiLineEqual(expected_text, self.writer.insert_file.getvalue())

    def testInsertsWithVariants(self):
        expected_text = """\
sample,region,qcut,left,insert,count
E1234_S1,R1,15,3,D,2
"""
        
        self.writer.add_read(offset_sequence='ACDEF', count=1)
        self.writer.add_read(offset_sequence='AFDEF', count=1)
        self.writer.write(inserts=[2])
        
        self.assertMultiLineEqual(expected_text, self.writer.insert_file.getvalue())

    def testDifferentInserts(self):
        expected_text = """\
sample,region,qcut,left,insert,count
E1234_S1,R1,15,3,D,2
E1234_S1,R1,15,3,F,3
"""
        
        self.writer.add_read(offset_sequence='ACDEF', count=2)
        self.writer.add_read(offset_sequence='ACFEF', count=3)
        self.writer.write(inserts=[2])
        
        self.assertMultiLineEqual(expected_text, self.writer.insert_file.getvalue())

    def testMulticharacterInsert(self):
        expected_text = """\
sample,region,qcut,left,insert,count
E1234_S1,R1,15,3,DE,1
"""
        
        self.writer.add_read(offset_sequence='ACDEF', count=1)
        self.writer.write(inserts=[2,3])
        
        self.assertMultiLineEqual(expected_text, self.writer.insert_file.getvalue())

    def testUnsortedInserts(self):
        expected_text = """\
sample,region,qcut,left,insert,count
E1234_S1,R1,15,3,DE,1
"""
        
        self.writer.add_read(offset_sequence='ACDEF', count=1)
        self.writer.write(inserts=(3, 2))
        
        self.assertMultiLineEqual(expected_text, self.writer.insert_file.getvalue())

class TranslateTest(unittest.TestCase):
    def testSingleCodon(self):
        nucs = 'TTT'
        expected_aminos = 'F'

        aminos = aln2counts.translate(nucs)
        
        self.assertEqual(expected_aminos, aminos)
        
    def testPartialCodon(self):
        nucs = 'TTTC'
        expected_aminos = 'F'

        aminos = aln2counts.translate(nucs)
        
        self.assertEqual(expected_aminos, aminos)
        
    def testTwoCodons(self):
        nucs = 'TTTCCT'
        expected_aminos = 'FP'

        aminos = aln2counts.translate(nucs)
        
        self.assertEqual(expected_aminos, aminos)
        
    def testOffset(self):
        nucs = "TTTCCT"
        offset = 3
        expected_aminos = "-FP"
        
        aminos = aln2counts.translate(nucs, offset)
        
        self.assertEqual(expected_aminos, aminos)
        
    def testSingleDashAmbiguous(self):
        nucs = '-TT'
        expected_aminos = '?'

        aminos = aln2counts.translate(nucs)
        
        self.assertEqual(expected_aminos, aminos)
        
    def testSingleDashUnambiguous(self):
        nucs = 'CG-' # CGA, CGC, CGG, CGT all map to R
        expected_aminos = 'R'

        aminos = aln2counts.translate(nucs)
        
        self.assertEqual(expected_aminos, aminos)
        
    def testTwoDashes(self):
        nucs = '--T'
        expected_aminos = '?'

        aminos = aln2counts.translate(nucs)
        
        self.assertEqual(expected_aminos, aminos)
        
    def testThreeDashes(self):
        nucs = '---'
        expected_aminos = '-'

        aminos = aln2counts.translate(nucs)
        
        self.assertEqual(expected_aminos, aminos)
        
    def testAmbiguousBasesThatAreSynonyms(self):
        nucs = 'TTY' # TTC or TTT: both map to F
        expected_aminos = 'F'

        aminos = aln2counts.translate(nucs)
        
        self.assertEqual(expected_aminos, aminos)
        
    def testTwoAmbiguousBasesThatAreSynonyms(self):
        nucs = 'MGR' # CGA, CGG, AGA, or AGG: all map to R
        expected_aminos = '?'

        aminos = aln2counts.translate(nucs)
        
        self.assertEqual(expected_aminos, aminos)

class SeedAminoTest(unittest.TestCase):
    def setUp(self):
        self.amino = aln2counts.SeedAmino(None)
    
    def testSingleRead(self):
        """ Read a single codon, and report on counts.
        Columns are:       A,C,D,E,F,G,H,I,K,L,M,N,P,Q,R,S,T,V,W,Y,*
        """
        nuc_seq = 'AAA' # -> K
        expected_counts = '0,0,0,0,0,0,0,0,8,0,0,0,0,0,0,0,0,0,0,0,0'
        
        self.amino.count_nucleotides(nuc_seq, 8)
        counts = self.amino.get_report()
        
        self.assertSequenceEqual(expected_counts, counts)
    
    def testDifferentCodon(self):
        """ Read two different codons, and report on counts.
        Columns are:       A,C,D,E,F,G,H,I,K,L,M,N,P,Q,R,S,T,V,W,Y,*
        """
        nuc_seq1 = 'AAA' # -> K
        nuc_seq2 = 'GGG' # -> G
        expected_counts = '0,0,0,0,0,5,0,0,8,0,0,0,0,0,0,0,0,0,0,0,0'
        
        self.amino.count_nucleotides(nuc_seq1, 8)
        self.amino.count_nucleotides(nuc_seq2, 5)
        counts = self.amino.get_report()
        
        self.assertSequenceEqual(expected_counts, counts)
    
    def testSameAminoAcid(self):
        """ Read same codon twice, and report on counts.
        Columns are:       A,C,D,E,F,G,H,I,K,L,M,N,P,Q,R,S,T,V,W,Y,*
        """
        nuc_seq1 = 'AAA' # -> K
        nuc_seq2 = 'AAG' # -> K
        expected_counts = '0,0,0,0,0,0,0,0,9,0,0,0,0,0,0,0,0,0,0,0,0'
        
        self.amino.count_nucleotides(nuc_seq1, 4)
        self.amino.count_nucleotides(nuc_seq2, 5)
        counts = self.amino.get_report()
        
        self.assertSequenceEqual(expected_counts, counts)
    
    def testNucleotides(self):
        nuc_seq1 = 'AAA' # -> K
        nuc_seq2 = 'AAG' # -> K
        expected_nuc_counts = '4,0,5,0'
        
        self.amino.count_nucleotides(nuc_seq1, 4)
        self.amino.count_nucleotides(nuc_seq2, 5)
        counts = self.amino.nucleotides[2].get_report()
        
        self.assertSequenceEqual(expected_nuc_counts, counts)
    
    def testConsensus(self):
        nuc_seq1 = 'AAA' # -> K
        nuc_seq2 = 'GGG' # -> G
        expected_consensus = 'G'
        
        self.amino.count_nucleotides(nuc_seq1, 4)
        self.amino.count_nucleotides(nuc_seq2, 5)
        consensus = self.amino.get_consensus()
        
        self.assertSequenceEqual(expected_consensus, consensus)
    
    def testConsensusMixture(self):
        nuc_seq1 = 'AAA' # -> K
        nuc_seq2 = 'GGG' # -> G
        nuc_seq3 = 'TTT' # -> F
        allowed_consensus_values = ('G', 'K')
        
        self.amino.count_nucleotides(nuc_seq1, 4)
        self.amino.count_nucleotides(nuc_seq2, 4)
        self.amino.count_nucleotides(nuc_seq3, 3)
        consensus = self.amino.get_consensus()
        
        self.assertIn(consensus, allowed_consensus_values)
    
    def testConsensusWithNoReads(self):
        consensus = self.amino.get_consensus()
        
        self.assertEqual(consensus, '-')
        
    def testMissingData(self):
        "Lower-case n represents a gap between the forward and reverse reads."
        
        nuc_seq = 'CTn'
        expected_consensus = 'L'
        
        self.amino.count_nucleotides(nuc_seq, 1)
        consensus = self.amino.get_consensus()
        
        self.assertEqual(expected_consensus, consensus)

class SeedNucleotideTest(unittest.TestCase):
    def setUp(self):
        self.nuc = aln2counts.SeedNucleotide()
    
    def testSingleRead(self):
        """ Read a single nucleotide, and report on counts.
        Columns are:       A,C,G,T
        """
        nuc_seq = 'C'
        expected_counts = '0,8,0,0'
        
        self.nuc.count_nucleotides(nuc_seq, 8)
        counts = self.nuc.get_report()
        
        self.assertSequenceEqual(expected_counts, counts)

    def testConsensusNoMixes(self):
        self.nuc.count_nucleotides('C', 1)
        consensus_max = self.nuc.get_consensus(aln2counts.MAX_CUTOFF)
        consensus_mix = self.nuc.get_consensus(0.1)

        expected_consensus = 'C'
        self.assertEqual(expected_consensus, consensus_max)
        self.assertEqual(expected_consensus, consensus_mix)

    def testConsensusMixed(self):
        self.nuc.count_nucleotides('C', 2)
        self.nuc.count_nucleotides('T', 1)
        consensus_max = self.nuc.get_consensus(aln2counts.MAX_CUTOFF)
        consensus_mix = self.nuc.get_consensus(0.1)

        expected_consensus_max = 'C'
        expected_consensus_mix = 'Y'
        self.assertEqual(expected_consensus_max, consensus_max)
        self.assertEqual(expected_consensus_mix, consensus_mix)

    def testConsensusMixedThree(self):
        self.nuc.count_nucleotides('C', 2)
        self.nuc.count_nucleotides('T', 1)
        self.nuc.count_nucleotides('G', 1)
        consensus_max = self.nuc.get_consensus(aln2counts.MAX_CUTOFF)
        consensus_mix = self.nuc.get_consensus(0.1)

        expected_consensus_max = 'C'
        expected_consensus_mix = 'B' # B is a mix of T, G, and C
        self.assertEqual(expected_consensus_max, consensus_max)
        self.assertEqual(expected_consensus_mix, consensus_mix)

    def testConsensusMixedAll(self):
        self.nuc.count_nucleotides('C', 2)
        self.nuc.count_nucleotides('T', 1)
        self.nuc.count_nucleotides('G', 1)
        self.nuc.count_nucleotides('A', 1)
        consensus_max = self.nuc.get_consensus(aln2counts.MAX_CUTOFF)
        consensus_mix = self.nuc.get_consensus(0.1)

        expected_consensus_max = 'C'
        expected_consensus_mix = 'N' # All four are reported as N
        self.assertEqual(expected_consensus_max, consensus_max)
        self.assertEqual(expected_consensus_mix, consensus_mix)

    def testConsensusMixedMax(self):
        self.nuc.count_nucleotides('C', 2)
        self.nuc.count_nucleotides('T', 2)
        self.nuc.count_nucleotides('G', 1)
        consensus_max = self.nuc.get_consensus(aln2counts.MAX_CUTOFF)
        consensus_mix = self.nuc.get_consensus(0.1)

        expected_consensus_max = 'Y' # C and T tie for max, mix is Y
        expected_consensus_mix = 'B' # C, T, and G mix is B
        self.assertEqual(expected_consensus_max, consensus_max)
        self.assertEqual(expected_consensus_mix, consensus_mix)

    def testConsensusCutoff(self):
        self.nuc.count_nucleotides('C', 2)
        self.nuc.count_nucleotides('T', 1)
        consensus_mix = self.nuc.get_consensus(0.5)

        expected_consensus = 'C' # T was below the cutoff
        self.assertEqual(expected_consensus, consensus_mix)

    def testConsensusCutoffAtBoundary(self):
        self.nuc.count_nucleotides('C', 9000)
        self.nuc.count_nucleotides('T', 1000)
        consensus_mix = self.nuc.get_consensus(0.1)

        expected_consensus = 'Y' # T was at the cutoff
        self.assertEqual(expected_consensus, consensus_mix)

    def testConsensusCutoffBelowBoundary(self):
        self.nuc.count_nucleotides('C', 9001)
        self.nuc.count_nucleotides('T', 999)
        consensus_mix = self.nuc.get_consensus(0.5)

        expected_consensus = 'C' # T was below the cutoff
        self.assertEqual(expected_consensus, consensus_mix)

    def testConsensusMixedWithPoorQuality(self):
        self.nuc.count_nucleotides('N', 2)
        self.nuc.count_nucleotides('T', 1)
        consensus_max = self.nuc.get_consensus(aln2counts.MAX_CUTOFF)
        consensus_mix = self.nuc.get_consensus(0.1)

        expected_consensus_max = 'T' # N always overruled
        expected_consensus_mix = 'T'
        self.assertEqual(expected_consensus_max, consensus_max)
        self.assertEqual(expected_consensus_mix, consensus_mix)

    def testConsensusMixedWithGap(self):
        self.nuc.count_nucleotides('-', 2)
        self.nuc.count_nucleotides('T', 1)
        consensus_max = self.nuc.get_consensus(aln2counts.MAX_CUTOFF)
        consensus_mix = self.nuc.get_consensus(0.1)

        expected_consensus_max = 'T' # dash always overruled
        expected_consensus_mix = 'T'
        self.assertEqual(expected_consensus_max, consensus_max)
        self.assertEqual(expected_consensus_mix, consensus_mix)

    def testConsensusMixedWithGapAndPoorQuality(self):
        self.nuc.count_nucleotides('N', 3)
        self.nuc.count_nucleotides('-', 2)
        self.nuc.count_nucleotides('T', 1)
        consensus_max = self.nuc.get_consensus(aln2counts.MAX_CUTOFF)
        consensus_mix = self.nuc.get_consensus(0.1)

        expected_consensus_max = 'T'
        expected_consensus_mix = 'T'
        self.assertEqual(expected_consensus_max, consensus_max)
        self.assertEqual(expected_consensus_mix, consensus_mix)

    def testConsensusPoorQualityOnly(self):
        self.nuc.count_nucleotides('N', 1)
        consensus_max = self.nuc.get_consensus(aln2counts.MAX_CUTOFF)
        consensus_mix = self.nuc.get_consensus(0.1)

        expected_consensus_max = 'N'
        expected_consensus_mix = 'N'
        self.assertEqual(expected_consensus_max, consensus_max)
        self.assertEqual(expected_consensus_mix, consensus_mix)

    def testConsensusMixedGapAndPoorQualityOnly(self):
        self.nuc.count_nucleotides('N', 3)
        self.nuc.count_nucleotides('-', 2)
        consensus_max = self.nuc.get_consensus(aln2counts.MAX_CUTOFF)
        consensus_mix = self.nuc.get_consensus(0.1)

        expected_consensus_max = 'N'
        expected_consensus_mix = 'N'
        self.assertEqual(expected_consensus_max, consensus_max)
        self.assertEqual(expected_consensus_mix, consensus_mix)

    def testConsensusAllBelowCutoff(self):
        self.nuc.count_nucleotides('C', 101)
        self.nuc.count_nucleotides('T', 100)
        self.nuc.count_nucleotides('G', 99)
        consensus_max = self.nuc.get_consensus(aln2counts.MAX_CUTOFF)
        consensus_mix = self.nuc.get_consensus(0.5)

        expected_consensus_max = 'C'
        expected_consensus_mix = 'N'
        self.assertEqual(expected_consensus_max, consensus_max)
        self.assertEqual(expected_consensus_mix, consensus_mix)

    def testConsensusBetweenReads(self):
        """Lower-case n represents the gap between forward and reverse reads.
        
        Should not be counted in consensus totals"""
        self.nuc.count_nucleotides('C', 9)
        self.nuc.count_nucleotides('T', 1)
        self.nuc.count_nucleotides('n', 2)
        consensus_mix = self.nuc.get_consensus(0.1)

        expected_consensus = 'Y'
        self.assertEqual(expected_consensus, consensus_mix)

    def testConsensusMissingPositions(self):
        "Positions that are never read are ignored in the consensus."
        
        #No counts added
        
        consensus_max = self.nuc.get_consensus(aln2counts.MAX_CUTOFF)
        consensus_mix = self.nuc.get_consensus(0.1)

        expected_consensus = ''
        self.assertEqual(expected_consensus, consensus_max)
        self.assertEqual(expected_consensus, consensus_mix)
