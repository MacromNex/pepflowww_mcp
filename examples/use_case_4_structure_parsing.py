#!/usr/bin/env python3
"""
UC-004: Protein Structure Parsing and Preprocessing

This script demonstrates parsing and preprocessing protein/peptide structures for use
with PepFlowww. It handles PDB file processing, sequence extraction, structure validation,
and data format conversion.

Usage:
    python examples/use_case_4_structure_parsing.py --pdb structure.pdb --output processed/

Input: PDB structure files (peptide-receptor complexes)
Output: Processed structure data, sequences, and validation reports
"""

import os
import sys
import argparse
import numpy as np
import pandas as pd
from pathlib import Path
from Bio.PDB import PDBParser, PDBIO, NeighborSearch, Selection

# Add PepFlowww to Python path
repo_root = Path(__file__).parent.parent / "repo" / "PepFlowww"
sys.path.insert(0, str(repo_root))

try:
    from pepflow.modules.protein.parsers import get_fasta_from_pdb
    from pepflow.modules.protein.writers import save_pdb
    from data.residue_constants import restypes, restype_order
    from data.protein import Protein
    import warnings
    warnings.filterwarnings("ignore")
except ImportError as e:
    print(f"Import Error: {e}")
    print("Please ensure the conda environment is activated and PepFlowww is properly installed")
    sys.exit(1)

def analyze_structure(pdb_path):
    """
    Analyze PDB structure to extract basic information

    Args:
        pdb_path (str): Path to PDB file

    Returns:
        dict: Structure analysis results
    """
    print(f"Analyzing structure: {pdb_path}")

    parser = PDBParser(QUIET=True)
    try:
        structure = parser.get_structure('structure', pdb_path)
    except Exception as e:
        print(f"Error parsing PDB file: {e}")
        return None

    results = {
        'pdb_path': pdb_path,
        'chains': [],
        'total_residues': 0,
        'total_atoms': 0,
        'resolution': None,
        'sequences': {}
    }

    # Extract chains and sequences
    for model in structure:
        for chain in model:
            chain_id = chain.get_id()
            residues = list(chain.get_residues())
            sequence = []

            for residue in residues:
                resname = residue.get_resname()
                if resname in restype_order:
                    sequence.append(resname)

            if sequence:  # Only include chains with amino acids
                results['chains'].append({
                    'chain_id': chain_id,
                    'length': len(sequence),
                    'sequence': sequence
                })
                results['sequences'][chain_id] = ''.join([
                    restypes[restype_order[res]] for res in sequence
                ])
                results['total_residues'] += len(sequence)

        # Count atoms
        for atom in structure.get_atoms():
            results['total_atoms'] += 1

    print(f"  Chains: {len(results['chains'])}")
    print(f"  Total residues: {results['total_residues']}")
    print(f"  Total atoms: {results['total_atoms']}")

    for chain_info in results['chains']:
        print(f"    Chain {chain_info['chain_id']}: {chain_info['length']} residues")

    return results

def identify_peptide_receptor(structure_analysis, max_peptide_length=30):
    """
    Identify which chains are peptides vs receptor proteins

    Args:
        structure_analysis (dict): Results from analyze_structure
        max_peptide_length (int): Maximum length to consider as peptide

    Returns:
        dict: Classification of chains
    """
    if not structure_analysis or not structure_analysis['chains']:
        return None

    chains = structure_analysis['chains']

    # Sort by length
    chains_sorted = sorted(chains, key=lambda x: x['length'])

    classification = {
        'peptide_chains': [],
        'receptor_chains': [],
        'unknown_chains': []
    }

    # Heuristic: shortest chain(s) likely to be peptide if under threshold
    for chain in chains_sorted:
        if chain['length'] <= max_peptide_length:
            classification['peptide_chains'].append(chain)
        else:
            classification['receptor_chains'].append(chain)

    print("Chain classification:")
    print(f"  Peptide chains: {[c['chain_id'] for c in classification['peptide_chains']]}")
    print(f"  Receptor chains: {[c['chain_id'] for c in classification['receptor_chains']]}")

    return classification

def extract_binding_interface(pdb_path, peptide_chain_ids, receptor_chain_ids, cutoff=10.0):
    """
    Extract binding interface residues between peptide and receptor

    Args:
        pdb_path (str): Path to PDB file
        peptide_chain_ids (list): List of peptide chain IDs
        receptor_chain_ids (list): List of receptor chain IDs
        cutoff (float): Distance cutoff for interface definition

    Returns:
        dict: Interface analysis results
    """
    print(f"Extracting binding interface (cutoff: {cutoff} Å)")

    parser = PDBParser(QUIET=True)
    structure = parser.get_structure('structure', pdb_path)

    # Get atoms from peptide and receptor chains
    peptide_atoms = []
    receptor_atoms = []

    for model in structure:
        for chain in model:
            chain_id = chain.get_id()
            if chain_id in peptide_chain_ids:
                peptide_atoms.extend(list(chain.get_atoms()))
            elif chain_id in receptor_chain_ids:
                receptor_atoms.extend(list(chain.get_atoms()))

    if not peptide_atoms or not receptor_atoms:
        print("  Warning: Could not find peptide or receptor atoms")
        return None

    # Find interface residues using neighbor search
    search = NeighborSearch(receptor_atoms)
    interface_residues = set()

    for atom in peptide_atoms:
        neighbors = search.search(atom.get_coord(), cutoff, level='R')
        for residue in neighbors:
            interface_residues.add(residue.get_full_id())

    print(f"  Found {len(interface_residues)} interface residues in receptor")

    # Get sequence of interface residues
    interface_sequence = []
    for model in structure:
        for chain in model:
            for residue in chain:
                if residue.get_full_id() in interface_residues:
                    resname = residue.get_resname()
                    if resname in restype_order:
                        interface_sequence.append(resname)

    results = {
        'num_interface_residues': len(interface_residues),
        'interface_residues': list(interface_residues),
        'interface_sequence': interface_sequence,
        'peptide_atoms': len(peptide_atoms),
        'receptor_atoms': len(receptor_atoms)
    }

    return results

def create_demo_structure():
    """
    Create a simple demo PDB structure for testing

    Returns:
        str: Path to demo PDB file
    """
    demo_pdb = "examples/data/structures/demo_peptide_receptor.pdb"
    os.makedirs(os.path.dirname(demo_pdb), exist_ok=True)

    # Simple demo structure with peptide and receptor
    pdb_content = """HEADER    DEMO PEPTIDE-RECEPTOR COMPLEX
ATOM      1  N   ALA A   1      -8.901   4.127  -0.555  1.00 11.99           N
ATOM      2  CA  ALA A   1      -8.608   3.135  -1.618  1.00 11.99           C
ATOM      3  C   ALA A   1      -7.221   2.458  -1.618  1.00 11.99           C
ATOM      4  O   ALA A   1      -6.632   2.248  -2.675  1.00 11.99           O
ATOM      5  CB  ALA A   1      -8.744   3.745  -2.987  1.00 11.99           C
ATOM      6  N   CYS A   2      -6.811   2.118  -0.418  1.00 11.99           N
ATOM      7  CA  CYS A   2      -5.516   1.468  -0.235  1.00 11.99           C
ATOM      8  C   CYS A   2      -4.375   2.324   0.285  1.00 11.99           C
ATOM      9  O   CYS A   2      -4.548   3.366   0.885  1.00 11.99           O
ATOM     10  CB  CYS A   2      -5.726   0.298   0.725  1.00 11.99           C
ATOM     11  SG  CYS A   2      -6.626  -1.111   0.078  1.00 11.99           S
ATOM     12  N   GLY A   3      -3.175   1.967  -0.015  1.00 11.99           N
ATOM     13  CA  GLY A   3      -1.999   2.705   0.466  1.00 11.99           C
ATOM     14  C   GLY A   3      -0.720   1.957   0.166  1.00 11.99           C
ATOM     15  O   GLY A   3      -0.627   0.746   0.286  1.00 11.99           O
ATOM     16  N   ALA B   1      10.000  10.000  10.000  1.00 20.00           N
ATOM     17  CA  ALA B   1      11.000  10.000  10.000  1.00 20.00           C
ATOM     18  C   ALA B   1      11.500  11.000  10.000  1.00 20.00           C
ATOM     19  O   ALA B   1      11.000  12.000  10.000  1.00 20.00           O
ATOM     20  CB  ALA B   1      11.500  10.000  11.000  1.00 20.00           C
END
"""

    with open(demo_pdb, 'w') as f:
        f.write(pdb_content)

    print(f"Created demo structure: {demo_pdb}")
    return demo_pdb

def process_structure(pdb_path, output_dir):
    """
    Complete structure processing pipeline

    Args:
        pdb_path (str): Path to input PDB file
        output_dir (str): Directory for output files

    Returns:
        dict: Processing results
    """
    print("=" * 50)
    print("Processing Structure")
    print("=" * 50)

    os.makedirs(output_dir, exist_ok=True)

    # Step 1: Analyze structure
    analysis = analyze_structure(pdb_path)
    if not analysis:
        return None

    # Step 2: Classify peptide vs receptor chains
    classification = identify_peptide_receptor(analysis)
    if not classification:
        return None

    # Step 3: Extract sequences
    print("\nExtracting sequences...")
    sequences_output = os.path.join(output_dir, "sequences.fasta")
    with open(sequences_output, 'w') as f:
        for chain_id, sequence in analysis['sequences'].items():
            chain_type = "peptide" if any(c['chain_id'] == chain_id for c in classification['peptide_chains']) else "receptor"
            f.write(f">{os.path.basename(pdb_path)}_{chain_id}_{chain_type}\n{sequence}\n")

    print(f"  Saved sequences to: {sequences_output}")

    # Step 4: Extract binding interface
    if classification['peptide_chains'] and classification['receptor_chains']:
        peptide_ids = [c['chain_id'] for c in classification['peptide_chains']]
        receptor_ids = [c['chain_id'] for c in classification['receptor_chains']]

        interface = extract_binding_interface(pdb_path, peptide_ids, receptor_ids)

        if interface:
            interface_output = os.path.join(output_dir, "interface_analysis.txt")
            with open(interface_output, 'w') as f:
                f.write(f"Binding Interface Analysis\n")
                f.write(f"========================\n\n")
                f.write(f"PDB File: {pdb_path}\n")
                f.write(f"Peptide Chains: {peptide_ids}\n")
                f.write(f"Receptor Chains: {receptor_ids}\n")
                f.write(f"Interface Residues: {interface['num_interface_residues']}\n")
                f.write(f"Interface Sequence: {''.join([restypes[restype_order[res]] for res in interface['interface_sequence']])}\n")

            print(f"  Saved interface analysis to: {interface_output}")

    # Step 5: Create summary report
    summary = {
        'pdb_file': pdb_path,
        'chains': len(analysis['chains']),
        'total_residues': analysis['total_residues'],
        'peptide_chains': len(classification['peptide_chains']),
        'receptor_chains': len(classification['receptor_chains']),
        'sequences_file': sequences_output
    }

    summary_output = os.path.join(output_dir, "structure_summary.txt")
    with open(summary_output, 'w') as f:
        f.write("Structure Processing Summary\n")
        f.write("===========================\n\n")
        for key, value in summary.items():
            f.write(f"{key}: {value}\n")

    print(f"  Saved summary to: {summary_output}")

    print("\nProcessing completed successfully!")
    return {
        'analysis': analysis,
        'classification': classification,
        'summary': summary,
        'output_dir': output_dir
    }

def main():
    parser = argparse.ArgumentParser(description="Parse and preprocess protein structures for PepFlowww")
    parser.add_argument('--pdb', type=str,
                       help='Path to input PDB file')
    parser.add_argument('--output', type=str, default='examples/processed_structure/',
                       help='Output directory for processed files')
    parser.add_argument('--max_peptide_length', type=int, default=30,
                       help='Maximum length to classify as peptide')
    parser.add_argument('--interface_cutoff', type=float, default=10.0,
                       help='Distance cutoff for interface definition (Angstroms)')
    parser.add_argument('--create_demo', action='store_true',
                       help='Create demo structure for testing')

    args = parser.parse_args()

    print("=" * 60)
    print("PepFlowww Structure Parsing and Preprocessing")
    print("=" * 60)

    # Create demo structure if requested
    if args.create_demo or not args.pdb:
        demo_pdb = create_demo_structure()
        if not args.pdb:
            args.pdb = demo_pdb

    # Check if PDB file exists
    if not os.path.exists(args.pdb):
        print(f"PDB file not found: {args.pdb}")
        print("Use --create_demo to create a demo structure for testing")
        return

    print(f"Input PDB: {args.pdb}")
    print(f"Output directory: {args.output}")
    print(f"Max peptide length: {args.max_peptide_length}")
    print(f"Interface cutoff: {args.interface_cutoff} Å")

    # Process the structure
    results = process_structure(args.pdb, args.output)

    if results:
        print("\n" + "=" * 60)
        print("PROCESSING SUMMARY")
        print("=" * 60)

        summary = results['summary']
        print(f"Input file: {summary['pdb_file']}")
        print(f"Total chains: {summary['chains']}")
        print(f"Total residues: {summary['total_residues']}")
        print(f"Peptide chains: {summary['peptide_chains']}")
        print(f"Receptor chains: {summary['receptor_chains']}")
        print(f"Output directory: {results['output_dir']}")

        print("\nFiles created:")
        for file in os.listdir(results['output_dir']):
            print(f"  {os.path.join(results['output_dir'], file)}")

        print("\nNext steps:")
        print("1. Validate the peptide/receptor classification")
        print("2. Use sequences for structure prediction or training")
        print("3. Use interface analysis to guide peptide design")
        print("4. Convert to PepFlowww data format for training/inference")

    else:
        print("Structure processing failed.")

if __name__ == '__main__':
    main()