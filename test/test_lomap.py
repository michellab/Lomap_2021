import unittest
from lomap.mcs import MCS
from rdkit import RDLogger,Chem
from lomap.dbmol import DBMolecules
from lomap import dbmol
import multiprocessing
import subprocess
import math
import argparse
import sys
import logging


def executable():
    return '/home/mark/.conan/data/Flare-Python/6.0/cresset/Python-3.6/package/90ee443cae5dd5c1b4861766ac14dc6fae231a92/bin/lomap'

def isclose(a,b):
    if (abs(a-b)>=1e-5):
        print("Value",a,"is not close to",b)
    return (abs(a-b)<1e-5)

class TestLomap(unittest.TestCase):
    """ Problem is the executable moves around, so hard to test
    def test_insufficient_arguments(self):
        cmd = [executable()]
        error_string = b'error: the following arguments are required: directory'
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = p.communicate()
        assert(error_string in stderr)
    """

    def test_mcsr(self):
        # MolA, molB, 3D?, max3d, mcsr, atomic_number_rule
        logging.basicConfig(format='%(message)s', level=logging.CRITICAL)
        data=[ ('test/transforms/phenyl.sdf','test/transforms/toluyl.sdf', False, 1000, math.exp(-0.1 * (6 + 7 - 2*6)), 1) ,
               ('test/transforms/phenyl.sdf','test/transforms/chlorophenyl.sdf', False, 1000, math.exp(-0.1 * (6 + 7 - 2*6)), 1) ,
               ('test/transforms/toluyl.sdf','test/transforms/chlorophenyl.sdf', False, 1000, 1, math.exp(-0.1 * 0.5)) ,
               ('test/transforms/toluyl.sdf','test/transforms/chlorophenol.sdf', False, 1000, math.exp(-0.1 * (7 + 8 - 2*7)), math.exp(-0.1 * 0.5)),
               ('test/transforms/phenyl.sdf','test/transforms/napthyl.sdf', False, 1000, math.exp(-0.1 * (8 + 12 - 2*8)), 1),
               ('test/transforms/chlorophenyl.sdf','test/transforms/fluorophenyl.sdf', False, 1000, 1, math.exp(-0.1 * 0.5 )),
               ('test/transforms/chlorophenyl.sdf','test/transforms/bromophenyl.sdf', False, 1000, 1, math.exp(-0.1 * 0.15)),
               ('test/transforms/chlorophenyl.sdf','test/transforms/iodophenyl.sdf', False, 1000, 1, math.exp(-0.1 * 0.35)),

               # Compare with and without 3D pruning
               ('test/transforms/chlorophenyl.sdf','test/transforms/chlorophenyl2.sdf', False, 1000, 1, 1),
               ('test/transforms/chlorophenyl.sdf','test/transforms/chlorophenyl2.sdf', False, 2, math.exp(-0.1 * (7 + 7 - 2*6)), 1) ,

               # Compare with and without 3D matching
               ('test/transforms/chlorotoluyl1.sdf','test/transforms/chlorotoluyl2.sdf', False, 1000, 1, 1),
               ('test/transforms/chlorotoluyl1.sdf','test/transforms/chlorotoluyl2.sdf', True, 1000, 1, math.exp(-0.05 * 2)) 
            ]


        lg = RDLogger.logger()
        lg.setLevel(RDLogger.CRITICAL)

        for d in data:
            mola = Chem.MolFromMolFile(d[0], sanitize=False, removeHs=False)
            molb = Chem.MolFromMolFile(d[1], sanitize=False, removeHs=False)
            MC = MCS(mola, molb, argparse.Namespace(time=20, verbose='info', max3d=d[3], threed=d[2]))
            mcsr = MC.mcsr()
            mncar = MC.mncar()
            atnum = MC.atomic_number_rule()
            strict = MC.tmcsr(strict_flag=True)
            loose = MC.tmcsr(strict_flag=False)

            assert(isclose(mcsr,d[4]))
            assert(isclose(atnum,d[5]))

    # Check iter and next
    def test_iter_next(self):
        logging.basicConfig(format='%(message)s', level=logging.CRITICAL)
        inst = DBMolecules('test/basic/', parallel=1, verbose='off', output=False, time=20, ecrscore=0.0, name='out',
                           display=False, max=6, cutoff=0.4, radial=False, hub=None)
        for i in range(0, inst.nums()):
            inst.next()
        with self.assertRaises(StopIteration):
            inst.next()


    # Check get, set and add
    def test_get_set_add(self):
        logging.basicConfig(format='%(message)s', level=logging.CRITICAL)
        inst = DBMolecules('test/basic/', parallel=1, verbose='off', output=False, time=20, ecrscore=0.0, name='out',
                           display=False, max=6, cutoff=0.4, radial=False, hub=None)
        with self.assertRaises(IndexError):
            inst.__getitem__(inst.nums()+1)
        with self.assertRaises(IndexError):
            inst.__setitem__(inst.nums()+1,inst[1])
        with self.assertRaises(ValueError):
            inst.__setitem__(0, 'no_mol_obj')
        with self.assertRaises(ValueError):
            inst.__add__('no_mol_obj')


    # Check serial and parallel mode
    def test_serial_parallel(self):
        logging.basicConfig(format='%(message)s', level=logging.CRITICAL)
        db = DBMolecules('test/basic')
        s_strict, s_loose = db.build_matrices()
        db.options.paralell = multiprocessing.cpu_count()
        p_strict, p_loose = db.build_matrices()
        
        assert (all(s_strict == p_strict))
        assert (all(s_loose == p_loose))


    def test_read_mol2_files(self):
        logging.basicConfig(format='%(message)s', level=logging.CRITICAL)
        db = DBMolecules('test/basic')
        db.options.directory = 'test/'
        with self.assertRaises(IOError):
            db.read_molecule_files()


    # Test which heterocycles I can grow (growing off a phenyl)
    # Test by Max indicates that growing complex heterocycles tends
    # to fail, so only allow growing phenyl, furan and pyrrole
    def test_heterocycle_scores(self):
        logging.basicConfig(format='%(message)s', level=logging.CRITICAL)
        testdata=[('phenylfuran.sdf',1),
                 ('phenylimidazole.sdf',math.exp(-0.1*4)),
                 ('phenylisoxazole.sdf',math.exp(-0.1*4)),
                 ('phenyloxazole.sdf',math.exp(-0.1*4)),
                 ('phenylpyrazole.sdf',math.exp(-0.1*4)),
                 ('phenylpyridine1.sdf',math.exp(-0.1*4)),
                 ('phenylpyridine2.sdf',math.exp(-0.1*4)),
                 ('phenylpyrimidine.sdf',math.exp(-0.1*4)),
                 ('phenylpyrrole.sdf',1),
                 ('phenylphenyl.sdf',1)]
        parent=Chem.MolFromMolFile('test/transforms/phenyl.sdf',sanitize=False, removeHs=False)
        lg = RDLogger.logger()
        lg.setLevel(RDLogger.CRITICAL)
        for d in testdata:
            comp=Chem.MolFromMolFile('test/transforms/'+d[0],sanitize=False, removeHs=False)
            MC=MCS(parent,comp)
            self.assertEqual(MC.heterocycles_rule(penalty=4),d[1],'Fail on heterocycle check for '+d[0])

    # Tests by Max indicate that growing a sulfonamide all in one go is 
    # dodgy, so disallow it
    def test_sulfonamide_scores(self):
        logging.basicConfig(format='%(message)s', level=logging.CRITICAL)
        testdata=[('cdk2_lig11.sdf',math.exp(-0.1*4)),
                 ('cdk2_lig1.sdf',1),
                 ('cdk2_lig2.sdf',math.exp(-0.1*4)),
                 ('cdk2_lig13.sdf',1),
                 ('cdk2_lig14.sdf',1),
                 ('cdk2_lig15.sdf',1) ]
        parent=Chem.MolFromMolFile('test/transforms/cdk2_lig16.sdf',sanitize=False, removeHs=False)
        lg = RDLogger.logger()
        lg.setLevel(RDLogger.CRITICAL)
        for d in testdata:
            comp=Chem.MolFromMolFile('test/transforms/'+d[0],sanitize=False, removeHs=False)
            MC=MCS(parent,comp)
            self.assertEqual(MC.sulfonamides_rule(penalty=4),d[1],'Fail on sulfonamide check for '+d[0])

    # Test to check symmetry equivalence by matching atomic numbers where possible
    def test_symmetry_matchheavies(self):
        logging.basicConfig(format='%(message)s', level=logging.CRITICAL)
        mol1 = Chem.MolFromMolFile('test/transforms/chlorophenol.sdf',sanitize=False, removeHs=False)
        mol2 = Chem.MolFromMolFile('test/transforms/chlorophenyl.sdf',sanitize=False, removeHs=False)
        mol3 = Chem.MolFromMolFile('test/transforms/chlorophenyl2.sdf',sanitize=False, removeHs=False)
        lg = RDLogger.logger()
        lg.setLevel(RDLogger.CRITICAL)
        MCS1 = MCS(mol1,mol2)
        MCS2 = MCS(mol2,mol3)
        MCS3 = MCS(mol1,mol3)
        self.assertEqual(MCS1.mcs_mol.GetNumHeavyAtoms(),9)
        self.assertEqual([int(at.GetProp('to_moli')) for at in MCS1.mcs_mol.GetAtoms()],[0, 5, 4, 3, 2, 1, 7, 6, 9]);
        self.assertEqual([int(at.GetProp('to_molj')) for at in MCS1.mcs_mol.GetAtoms()],[0, 5, 4, 3, 2, 1, 7, 6, 8]);
        self.assertEqual([int(at.GetProp('to_moli')) for at in MCS2.mcs_mol.GetAtoms()],[0, 5, 4, 3, 2, 1, 7, 6, 8]);
        self.assertEqual([int(at.GetProp('to_molj')) for at in MCS2.mcs_mol.GetAtoms()],[4, 5, 0, 1, 2, 3, 7, 6, 8]);
        self.assertEqual([int(at.GetProp('to_moli')) for at in MCS3.mcs_mol.GetAtoms()],[4, 5, 0, 1, 2, 3, 7, 6, 9]);
        self.assertEqual([int(at.GetProp('to_molj')) for at in MCS3.mcs_mol.GetAtoms()],[0, 5, 4, 3, 2, 1, 7, 6, 8]);

    
    # Test to check symmetry equivalence by matching 3D coordinates rather than atomic numbers
    def test_symmetry_match3d(self):
        logging.basicConfig(format='%(message)s', level=logging.CRITICAL)
        mol1 = Chem.MolFromMolFile('test/transforms/chlorophenol.sdf',sanitize=False, removeHs=False)
        mol2 = Chem.MolFromMolFile('test/transforms/chlorophenyl.sdf',sanitize=False, removeHs=False)
        mol3 = Chem.MolFromMolFile('test/transforms/chlorophenyl2.sdf',sanitize=False, removeHs=False)
        lg = RDLogger.logger()
        lg.setLevel(RDLogger.CRITICAL)
        MCS1 = MCS(mol1,mol2,options=argparse.Namespace(time=20, verbose='info', max3d=1000, threed=True))
        MCS2 = MCS(mol2,mol3,options=argparse.Namespace(time=20, verbose='info', max3d=1000, threed=True))
        MCS3 = MCS(mol1,mol3,options=argparse.Namespace(time=20, verbose='info', max3d=1000, threed=True))
        self.assertEqual(MCS1.mcs_mol.GetNumHeavyAtoms(),9)
        # MCS1 and MCS2 are the same as in the matchheavies case, but MCS3 gives a diffrent answer
        self.assertEqual([int(at.GetProp('to_moli')) for at in MCS1.mcs_mol.GetAtoms()],[0, 5, 4, 3, 2, 1, 7, 6, 9]);
        self.assertEqual([int(at.GetProp('to_molj')) for at in MCS1.mcs_mol.GetAtoms()],[0, 5, 4, 3, 2, 1, 7, 6, 8]);
        self.assertEqual([int(at.GetProp('to_moli')) for at in MCS2.mcs_mol.GetAtoms()],[0, 5, 4, 3, 2, 1, 7, 6, 8]);
        self.assertEqual([int(at.GetProp('to_molj')) for at in MCS2.mcs_mol.GetAtoms()],[4, 5, 0, 1, 2, 3, 7, 6, 8]);
        self.assertEqual([int(at.GetProp('to_moli')) for at in MCS3.mcs_mol.GetAtoms()],[0, 5, 4, 3, 2, 1, 8, 6, 9]);
        self.assertEqual([int(at.GetProp('to_molj')) for at in MCS3.mcs_mol.GetAtoms()],[0, 5, 4, 3, 2, 1, 7, 6, 8]);

    # Test to check removing atoms from the MCS when the 3D coords are too far apart
    def test_clip_on_3d(self):
        logging.basicConfig(format='%(message)s', level=logging.CRITICAL)
        mol1 = Chem.MolFromMolFile('test/transforms/chlorophenyl.sdf',sanitize=False, removeHs=False)
        mol2 = Chem.MolFromMolFile('test/transforms/chlorophenyl2.sdf',sanitize=False, removeHs=False)
        lg = RDLogger.logger()
        lg.setLevel(RDLogger.CRITICAL)
        MCS1 = MCS(mol1,mol2,options=argparse.Namespace(time=20, verbose='info', max3d=1000, threed=True))
        MCS2 = MCS(mol1,mol2,options=argparse.Namespace(time=20, verbose='info', max3d=2, threed=True))
        self.assertEqual(MCS1.mcs_mol.GetNumHeavyAtoms(),9)
        self.assertEqual(MCS2.mcs_mol.GetNumHeavyAtoms(),8)

    # Test disallowing turning a methyl group (or larger) into a ring atom
    def test_transmuting_methyl_into_ring_rule(self):
        logging.basicConfig(format='%(message)s', level=logging.CRITICAL)
        testdata=[('phenyl.sdf','toluyl3.sdf',1),
                 ('toluyl3.sdf','chlorotoluyl1.sdf',1),
                 ('toluyl3.sdf','phenylfuran.sdf',math.exp(-0.1*4)),
                 ('toluyl3.sdf','phenylpyridine1.sdf',math.exp(-0.1*4)),
                 ('phenyl.sdf','phenylfuran.sdf',1),
                 ('phenyl.sdf','phenylpyridine1.sdf',1),
                 ('chlorophenol.sdf','phenylfuran.sdf',1)
                 ]
        lg = RDLogger.logger()
        lg.setLevel(RDLogger.CRITICAL)
        for d in testdata:
            parent=Chem.MolFromMolFile('test/transforms/'+d[0],sanitize=False, removeHs=False)
            comp=Chem.MolFromMolFile('test/transforms/'+d[1],sanitize=False, removeHs=False)
            MC=MCS(parent,comp)
            self.assertEqual(MC.transmuting_methyl_into_ring_rule(penalty=4),d[2],'Fail on transmuting-methyl-to-ring check for '+d[0]+' '+d[1])

    # Test penalising hybridization changes
    def test_hybridization_rule(self):
        logging.basicConfig(format='%(message)s', level=logging.CRITICAL)
        testdata=[('napthyl.sdf','tetrahydronaphthyl.sdf',math.exp(-0.1 * 4))
                 ]
        lg = RDLogger.logger()
        lg.setLevel(RDLogger.CRITICAL)
        for d in testdata:
            parent=Chem.MolFromMolFile('test/transforms/'+d[0],sanitize=False, removeHs=False)
            comp=Chem.MolFromMolFile('test/transforms/'+d[1],sanitize=False, removeHs=False)
            MC=MCS(parent,comp)
            assert(isclose(MC.hybridization_rule(1.0),d[2]))

    # Test disallowing turning a ring into an incompatible ring
    def test_transmuting_ring_sizes_rule(self):
        logging.basicConfig(format='%(message)s', level=logging.CRITICAL)
        testdata=[('phenyl.sdf','phenylcyclopropyl.sdf',1),
                 ('toluyl.sdf','phenylcyclopropyl.sdf',1),  # Disallowed by test_transmuting_methyl_into_ring_rule instead
                 ('phenylcyclopropyl.sdf','phenylcyclobutyl.sdf',0),
                 ('phenylcyclopropyl.sdf','phenylcyclopentyl.sdf',0),
                 ('phenylcyclopropyl.sdf','phenylcyclononyl.sdf',0),
                 ('phenylcyclobutyl.sdf','phenylcyclopentyl.sdf',0),
                 ('phenylcyclobutyl.sdf','phenylcyclononyl.sdf',0),
                 ('phenylcyclopentyl.sdf','phenylcyclononyl.sdf',1)
                 ]
        lg = RDLogger.logger()
        lg.setLevel(RDLogger.CRITICAL)
        for d in testdata:
            parent=Chem.MolFromMolFile('test/transforms/'+d[0],sanitize=False, removeHs=False)
            comp=Chem.MolFromMolFile('test/transforms/'+d[1],sanitize=False, removeHs=False)
            MC=MCS(parent,comp)
            self.assertEqual(MC.transmuting_ring_sizes_rule(),d[2],'Fail on transmuting-ring-size check for '+d[0]+' '+d[1])

    # Test getting the mapping string out of the MCS
    def test_mapping_string_heavy(self):
        logging.basicConfig(format='%(message)s', level=logging.CRITICAL)
        testdata=[('phenyl.sdf','toluyl3.sdf',"0:0,1:1,2:2,3:3,4:4,5:5,6:6,7:7"),
                 ('toluyl2.sdf','chlorotoluyl1.sdf',"0:0,1:1,2:2,3:3,4:4,5:5,6:6,7:8,8:9"),
                 ('toluyl3.sdf','phenylfuran.sdf',"0:0,1:1,2:2,3:3,4:4,5:5,6:6,7:7")
                 ]
        lg = RDLogger.logger()
        lg.setLevel(RDLogger.CRITICAL)
        for d in testdata:
            parent=Chem.MolFromMolFile('test/transforms/'+d[0],sanitize=False, removeHs=False)
            comp=Chem.MolFromMolFile('test/transforms/'+d[1],sanitize=False, removeHs=False)
            MC=MCS(parent,comp)
            self.assertEqual(MC.heavy_atom_match_list(), d[2], 'Fail on heavy atom match list for '+d[0]+' '+d[1])

    # Test getting the mapping string including hydrogens out of the MCS
    def test_mapping_string_hydrogen(self):
        logging.basicConfig(format='%(message)s', level=logging.CRITICAL)
        testdata=[('phenyl.sdf','toluyl3.sdf',"0:0,1:1,2:2,3:3,4:4,5:5,6:6,7:7,8:9,9:10,10:8,11:11,12:17,13:12,14:13,15:14,16:15,17:16"),
                 ('toluyl2.sdf','chlorotoluyl1.sdf',"0:0,1:1,2:2,3:3,4:4,5:5,6:6,7:8,8:9,9:10,10:7,11:11,12:12,13:13,14:14,15:15,16:16,17:17,18:18,19:19,20:20"),
                 ('toluyl3.sdf','phenylfuran.sdf',"0:0,1:1,2:2,3:3,4:4,5:5,6:6,7:7,9:13,10:14,11:15,12:17,13:18,14:19,15:20,16:21,17:16"),
                 ('toluyl.sdf','phenylmethylamino.sdf',"0:0,1:1,2:2,3:3,4:4,5:5,6:6,7:7,8:8,9:10,10:11,11:12,12:13,13:14,14:15,15:16,16:17,17:18,18:9,19:19,20:20")
                 ]
        lg = RDLogger.logger()
        lg.setLevel(RDLogger.CRITICAL)
        for d in testdata:
            parent=Chem.MolFromMolFile('test/transforms/'+d[0],sanitize=False, removeHs=False)
            comp=Chem.MolFromMolFile('test/transforms/'+d[1],sanitize=False, removeHs=False)
            MC=MCS(parent,comp)
            self.assertEqual(MC.all_atom_match_list(), d[2], 'Fail on all-atom match list for '+d[0]+' '+d[1])
    
    # Test to check correct handling of chirality
    def test_chirality_handling(self):
        logging.basicConfig(format='%(message)s', level=logging.CRITICAL)
        testdata=[('Chiral1R.sdf','Chiral1S.sdf',6),
                  ('Chiral1R.sdf','Chiral2R.sdf',7),
                  ('Chiral1S.sdf','Chiral2R.sdf',6),
                  ('Chiral3RS.sdf','Chiral3SS.sdf',11),
                  ('Chiral3SR.sdf','Chiral3SS.sdf',10),
                  ('Chiral3SR.sdf','Chiral3RS.sdf',9),
                  ('Chiral4RR.sdf','Chiral4RS.sdf',5),
                  ('RingChiralR.sdf','RingChiralS.sdf',6),
                  ('SpiroR.sdf','SpiroS.sdf',6),
                  ('bace_mk1.sdf','bace_cat_13d.sdf',21),   # Bug found in BACE data set
                  ('bace_cat_13d.sdf','bace_mk1.sdf',21),   # check both ways round
                  ('bace_mk1.sdf','bace_cat_13d_perm1.sdf',21), # Check unaffected by atom order
                  ('bace_mk1.sdf','bace_cat_13d_perm2.sdf',21),
                  ('bace_mk1.sdf','bace_cat_13d_perm3.sdf',21),
                  ('bace_mk1.sdf','bace_cat_13d_perm4.sdf',21),
                  ('bace_mk1.sdf','bace_cat_13d_perm5.sdf',21),
                  ('bace_cat_13d_inverted.sdf','bace_mk1.sdf',13),  # Check that we do pick up the inverted case OK
                  ('bace_cat_13d.sdf','bace_cat_13d_inverted.sdf',13) # Check normal vs inverted
                ]
        lg = RDLogger.logger()
        lg.setLevel(RDLogger.INFO)
        for d in testdata:
            parent=Chem.MolFromMolFile('test/chiral/'+d[0],sanitize=False, removeHs=False)
            comp=Chem.MolFromMolFile('test/chiral/'+d[1],sanitize=False, removeHs=False)
            MC=MCS(parent,comp, argparse.Namespace(time=20, verbose='info', max3d=5, threed=True))
            self.assertEqual(MC.mcs_mol.GetNumHeavyAtoms(), d[2], 'Fail on chiral MCS size for '+d[0]+' '+d[1])

    # Test to check correct trimming of rings when 3D coordinate matching is used
    def test_ring_trimming_on_3d_match(self):
        logging.basicConfig(format='%(message)s', level=logging.CRITICAL)
        parent=Chem.MolFromMolFile('test/transforms/phenylcyclopentylmethyl1.sdf',sanitize=False, removeHs=False)
        comp=Chem.MolFromMolFile('test/transforms/phenylcyclopentylmethyl2.sdf',sanitize=False, removeHs=False)
        MC=MCS(parent,comp, argparse.Namespace(time=20, verbose='info', max3d=2, threed=True))
        self.assertEqual(MC.mcs_mol.GetNumHeavyAtoms(), 9, 'Fail on ring trim on 3D match')

    # Test to check handling of the alpha- vs beta-naphthyl bug
    def test_rdkit_broken_mcs_fix(self):
        logging.basicConfig(format='%(message)s', level=logging.CRITICAL)
        parent=Chem.MolFromMolFile('test/transforms/napthyl2.sdf',sanitize=False, removeHs=False)
        comp=Chem.MolFromMolFile('test/transforms/napthyl3.sdf',sanitize=False, removeHs=False)
        MC=MCS(parent,comp, argparse.Namespace(time=20, verbose='info', max3d=0, threed=False))
        self.assertLess(MC.mcs_mol.GetNumHeavyAtoms(), 25, 'Fail on detecting broken RDkit MCS on fused ring')

    # Test to check handling of mapping to prochiral hydrogens
    def test_mapping_prochiral_hydrogen(self):
        logging.basicConfig(format='%(message)s', level=logging.CRITICAL)
        parent=Chem.MolFromMolFile('test/chiral/tpbs2_lig1.sdf',sanitize=False, removeHs=False)
        parent2=Chem.MolFromMolFile('test/chiral/tpbs2_lig1a.sdf',sanitize=False, removeHs=False)   # Atom ordering changed
        comp=Chem.MolFromMolFile('test/chiral/tpbs2_lig2.sdf',sanitize=False, removeHs=False)
        MC=MCS(parent,comp, argparse.Namespace(time=20, verbose='info', max3d=3, threed=True))
        # Check that the correct prochiral hydrogen matches the bridging carbons
        assert("51:12" in MC.all_atom_match_list())
        assert("35:11" in MC.all_atom_match_list())
        MC=MCS(parent2,comp, argparse.Namespace(time=20, verbose='info', max3d=3, threed=True))
        # parent2 is the same mol as parent1, except that atoms 34 and 35 were swapped
        assert("51:12" in MC.all_atom_match_list())
        assert("34:11" in MC.all_atom_match_list())

    def fields_for_link(self, mola, molb):
        """ Parse the out_score_with_connection.txt file, find the line for mola to molb, and return its fields. """
        with open('out_score_with_connection.txt','r') as f:
            for line in f.readlines():
                fields = line.replace(",","").split()
                if ((fields[2]==mola and fields[3]==molb) or (fields[3]==mola and fields[2]==molb)):
                    return fields
        return []

    def score_for_link(self, mola, molb):
        return float(self.fields_for_link(mola,molb)[4])
            
    def test_complete_run(self):
        logging.basicConfig(format='%(message)s', level=logging.CRITICAL)
        progname=sys.argv[0]
        sys.argv=[progname,'-o','--output-no-images','--output-no-graph','test/linksfile']
        dbmol.startup()
        # Check scores
        assert(isclose(self.score_for_link('phenyl.sdf','phenylcyclobutyl.sdf'),0.67032))
        assert(isclose(self.score_for_link('phenyl.sdf','phenylfuran.sdf'),0.60653))
        assert(isclose(self.score_for_link('phenyl.sdf','toluyl.sdf'),0.90484))
        assert(isclose(self.score_for_link('phenylcyclobutyl.sdf','phenylfuran.sdf'),0.40657))
        assert(isclose(self.score_for_link('phenylcyclobutyl.sdf','toluyl.sdf'),0.33287))
        assert(isclose(self.score_for_link('phenylfuran.sdf','toluyl.sdf'),0.54881))
        # Check connections
        self.assertEqual(self.fields_for_link('phenyl.sdf','phenylcyclobutyl.sdf')[7],"Yes")
        self.assertEqual(self.fields_for_link('phenyl.sdf','phenylfuran.sdf')[7],"No")
        self.assertEqual(self.fields_for_link('phenyl.sdf','toluyl.sdf')[7],"Yes")
        self.assertEqual(self.fields_for_link('phenylcyclobutyl.sdf','phenylfuran.sdf')[7],"Yes")
        self.assertEqual(self.fields_for_link('phenylcyclobutyl.sdf','toluyl.sdf')[7],"No")
        self.assertEqual(self.fields_for_link('phenylfuran.sdf','toluyl.sdf')[7],"Yes")

    def test_complete_run_parallel(self):
        '''Test running in parallel mode with 5 subprocesses.'''
        logging.basicConfig(format='%(message)s', level=logging.CRITICAL)
        progname=sys.argv[0]
        sys.argv=[progname,'-o','-p','5','--output-no-images','--output-no-graph','test/linksfile']
        dbmol.startup()
        # Check scores
        assert(isclose(self.score_for_link('phenyl.sdf','phenylcyclobutyl.sdf'),0.67032))
        assert(isclose(self.score_for_link('phenyl.sdf','phenylfuran.sdf'),0.60653))
        assert(isclose(self.score_for_link('phenyl.sdf','toluyl.sdf'),0.90484))
        assert(isclose(self.score_for_link('phenylcyclobutyl.sdf','phenylfuran.sdf'),0.40657))
        assert(isclose(self.score_for_link('phenylcyclobutyl.sdf','toluyl.sdf'),0.33287))
        assert(isclose(self.score_for_link('phenylfuran.sdf','toluyl.sdf'),0.54881))
        # Check connections
        self.assertEqual(self.fields_for_link('phenyl.sdf','phenylcyclobutyl.sdf')[7],"Yes")
        self.assertEqual(self.fields_for_link('phenyl.sdf','phenylfuran.sdf')[7],"No")
        self.assertEqual(self.fields_for_link('phenyl.sdf','toluyl.sdf')[7],"Yes")
        self.assertEqual(self.fields_for_link('phenylcyclobutyl.sdf','phenylfuran.sdf')[7],"Yes")
        self.assertEqual(self.fields_for_link('phenylcyclobutyl.sdf','toluyl.sdf')[7],"No")
        self.assertEqual(self.fields_for_link('phenylfuran.sdf','toluyl.sdf')[7],"Yes")

    def test_linksfile(self):
        """ Test a linksfile forcing a link from phenyl to phenylfuran. """
        logging.basicConfig(format='%(message)s', level=logging.CRITICAL)
        progname=sys.argv[0]
        sys.argv=[progname,'-o','--output-no-images','--output-no-graph','--links-file','test/linksfile/links1.txt','test/linksfile']
        dbmol.startup()
        # Check scores
        assert(isclose(self.score_for_link('phenyl.sdf','phenylcyclobutyl.sdf'),0.67032))
        assert(isclose(self.score_for_link('phenyl.sdf','phenylfuran.sdf'),0.60653))
        assert(isclose(self.score_for_link('phenyl.sdf','toluyl.sdf'),0.90484))
        assert(isclose(self.score_for_link('phenylcyclobutyl.sdf','phenylfuran.sdf'),0.40657))
        assert(isclose(self.score_for_link('phenylcyclobutyl.sdf','toluyl.sdf'),0.33287))
        assert(isclose(self.score_for_link('phenylfuran.sdf','toluyl.sdf'),0.54881))
        # Check connections
        self.assertEqual(self.fields_for_link('phenyl.sdf','phenylcyclobutyl.sdf')[7],"Yes")
        self.assertEqual(self.fields_for_link('phenyl.sdf','phenylfuran.sdf')[7],"Yes")
        self.assertEqual(self.fields_for_link('phenyl.sdf','toluyl.sdf')[7],"Yes")
        self.assertEqual(self.fields_for_link('phenylcyclobutyl.sdf','phenylfuran.sdf')[7],"Yes")
        self.assertEqual(self.fields_for_link('phenylcyclobutyl.sdf','toluyl.sdf')[7],"No")
        self.assertEqual(self.fields_for_link('phenylfuran.sdf','toluyl.sdf')[7],"Yes")

    def test_linksfile_scores(self):
        """ Test a linksfile forcing prespecified scores for some links."""
        logging.basicConfig(format='%(message)s', level=logging.CRITICAL)
        progname=sys.argv[0]
        sys.argv=[progname,'-o','--output-no-images','--output-no-graph','--links-file','test/linksfile/links2.txt','test/linksfile']
        dbmol.startup()
        # Check scores
        assert(isclose(self.score_for_link('phenyl.sdf','phenylcyclobutyl.sdf'),0.67032))
        assert(isclose(self.score_for_link('phenyl.sdf','phenylfuran.sdf'),0.77777))    # Forced from linksfile
        assert(isclose(self.score_for_link('phenyl.sdf','toluyl.sdf'),0.88888))         # Forced from linksfile
        assert(isclose(self.score_for_link('phenylcyclobutyl.sdf','phenylfuran.sdf'),0.40657))
        assert(isclose(self.score_for_link('phenylcyclobutyl.sdf','toluyl.sdf'),0.33287))
        assert(isclose(self.score_for_link('phenylfuran.sdf','toluyl.sdf'),0.54881))
        # Check connections
        self.assertEqual(self.fields_for_link('phenyl.sdf','phenylcyclobutyl.sdf')[7],"Yes")
        self.assertEqual(self.fields_for_link('phenyl.sdf','phenylfuran.sdf')[7],"No")
        self.assertEqual(self.fields_for_link('phenyl.sdf','toluyl.sdf')[7],"Yes")
        self.assertEqual(self.fields_for_link('phenylcyclobutyl.sdf','phenylfuran.sdf')[7],"Yes")
        self.assertEqual(self.fields_for_link('phenylcyclobutyl.sdf','toluyl.sdf')[7],"No")
        self.assertEqual(self.fields_for_link('phenylfuran.sdf','toluyl.sdf')[7],"Yes")

    def test_linksfile_scores_force(self):
        """ Test a linksfile forcing prespecified scores and link inclusion for some links."""
        logging.basicConfig(format='%(message)s', level=logging.CRITICAL)
        progname=sys.argv[0]
        sys.argv=[progname,'-o','--output-no-images','--output-no-graph','--links-file','test/linksfile/links3.txt','test/linksfile']
        dbmol.startup()
        # Check scores
        assert(isclose(self.score_for_link('phenyl.sdf','phenylcyclobutyl.sdf'),0.1))
        assert(isclose(self.score_for_link('phenyl.sdf','phenylfuran.sdf'),0.2))
        assert(isclose(self.score_for_link('phenyl.sdf','toluyl.sdf'),0.3))
        assert(isclose(self.score_for_link('phenylcyclobutyl.sdf','phenylfuran.sdf'),0.4))
        assert(isclose(self.score_for_link('phenylcyclobutyl.sdf','toluyl.sdf'),0.5))
        assert(isclose(self.score_for_link('phenylfuran.sdf','toluyl.sdf'),0.6))
        # Check connections
        self.assertEqual(self.fields_for_link('phenyl.sdf','phenylcyclobutyl.sdf')[7],"Yes")
        self.assertEqual(self.fields_for_link('phenyl.sdf','phenylfuran.sdf')[7],"Yes")
        self.assertEqual(self.fields_for_link('phenyl.sdf','toluyl.sdf')[7],"No")
        self.assertEqual(self.fields_for_link('phenylcyclobutyl.sdf','phenylfuran.sdf')[7],"Yes")
        self.assertEqual(self.fields_for_link('phenylcyclobutyl.sdf','toluyl.sdf')[7],"Yes")
        self.assertEqual(self.fields_for_link('phenylfuran.sdf','toluyl.sdf')[7],"Yes")

    def test_no_cycle_cover(self):
        logging.basicConfig(format='%(message)s', level=logging.CRITICAL)
        progname=sys.argv[0]
        sys.argv=[progname,'-o','-T','--output-no-images','--output-no-graph','test/linksfile']
        dbmol.startup()
        # Check connections
        self.assertEqual(self.fields_for_link('phenyl.sdf','phenylcyclobutyl.sdf')[7],"Yes")
        self.assertEqual(self.fields_for_link('phenyl.sdf','phenylfuran.sdf')[7],"Yes")
        self.assertEqual(self.fields_for_link('phenyl.sdf','toluyl.sdf')[7],"Yes")
        self.assertEqual(self.fields_for_link('phenylcyclobutyl.sdf','phenylfuran.sdf')[7],"No")
        self.assertEqual(self.fields_for_link('phenylcyclobutyl.sdf','toluyl.sdf')[7],"No")
        self.assertEqual(self.fields_for_link('phenylfuran.sdf','toluyl.sdf')[7],"No")


if __name__ == '__main__':
    unittest.main()
           
