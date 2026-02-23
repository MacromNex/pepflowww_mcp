#!/usr/bin/env python3
"""
UC-005: Peptide Sequence Analysis and Property Prediction

This script demonstrates analysis of cyclic peptide sequences, including sequence
statistics, physicochemical properties, structural features, and druggability
assessment using PepFlowww utilities.

Usage:
    python examples/use_case_5_peptide_analysis.py --sequences peptides.fasta --output analysis/

Input: Peptide sequences (FASTA format or individual sequences)
Output: Analysis reports, property predictions, and visualizations
"""

import os
import sys
import argparse
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from collections import Counter

# Add PepFlowww to Python path
repo_root = Path(__file__).parent.parent / "repo" / "PepFlowww"
sys.path.insert(0, str(repo_root))

try:
    from data.residue_constants import restypes, restype_order, restype_num
    import warnings
    warnings.filterwarnings("ignore")
except ImportError as e:
    print(f"Import Error: {e}")
    print("Please ensure the conda environment is activated and PepFlowww is properly installed")
    sys.exit(1)

# Amino acid properties
AA_PROPERTIES = {
    'hydrophobic': ['A', 'V', 'I', 'L', 'M', 'F', 'W', 'Y'],
    'polar': ['S', 'T', 'N', 'Q'],
    'positive': ['K', 'R', 'H'],
    'negative': ['D', 'E'],
    'special': ['C', 'P', 'G'],
    'molecular_weight': {
        'A': 89.1, 'R': 174.2, 'N': 132.1, 'D': 133.1, 'C': 121.2,
        'Q': 146.1, 'E': 147.1, 'G': 75.1, 'H': 155.2, 'I': 131.2,
        'L': 131.2, 'K': 146.2, 'M': 149.2, 'F': 165.2, 'P': 115.1,
        'S': 105.1, 'T': 119.1, 'W': 204.2, 'Y': 181.2, 'V': 117.1
    },
    'hydrophobicity': {  # Kyte-Doolittle scale
        'A': 1.8, 'R': -4.5, 'N': -3.5, 'D': -3.5, 'C': 2.5,
        'Q': -3.5, 'E': -3.5, 'G': -0.4, 'H': -3.2, 'I': 4.5,
        'L': 3.8, 'K': -3.9, 'M': 1.9, 'F': 2.8, 'P': -1.6,
        'S': -0.8, 'T': -0.7, 'W': -0.9, 'Y': -1.3, 'V': 4.2
    }
}

def read_sequences_from_fasta(fasta_path):
    """
    Read peptide sequences from FASTA file

    Args:
        fasta_path (str): Path to FASTA file

    Returns:
        dict: Dictionary of sequence_id -> sequence
    """
    sequences = {}
    current_id = None
    current_seq = ""

    with open(fasta_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line.startswith('>'):
                if current_id is not None:
                    sequences[current_id] = current_seq
                current_id = line[1:]  # Remove '>'
                current_seq = ""
            else:
                current_seq += line

        # Add last sequence
        if current_id is not None:
            sequences[current_id] = current_seq

    return sequences

def create_demo_sequences():
    """
    Create demo peptide sequences for analysis

    Returns:
        dict: Demo sequences
    """
    demo_sequences = {
        'cyclic_peptide_1': 'CYCLIGKRC',
        'cyclic_peptide_2': 'ACDEFGHIK',
        'cyclic_peptide_3': 'RVTWYKLPC',
        'cyclic_peptide_4': 'GFPSWQNMC',
        'cyclic_peptide_5': 'ALTDHENVC',
        'linear_control': 'GPGPGPGPGP',
        'antimicrobial': 'RRWWRFKKLR',
        'cell_penetrating': 'RRRQRRKKRG'
    }

    # Save demo sequences
    fasta_path = 'examples/data/sequences/demo_peptides.fasta'
    os.makedirs(os.path.dirname(fasta_path), exist_ok=True)

    with open(fasta_path, 'w') as f:
        for seq_id, sequence in demo_sequences.items():
            f.write(f'>{seq_id}\n{sequence}\n')

    print(f"Created demo sequences: {fasta_path}")
    return demo_sequences

def analyze_sequence_composition(sequences):
    """
    Analyze amino acid composition of sequences

    Args:
        sequences (dict): Dictionary of sequence_id -> sequence

    Returns:
        pd.DataFrame: Composition analysis
    """
    print("Analyzing sequence composition...")

    composition_data = []

    for seq_id, sequence in sequences.items():
        sequence = sequence.upper()
        length = len(sequence)

        # Count amino acids
        aa_counts = Counter(sequence)

        # Calculate percentages
        composition = {aa: 0.0 for aa in restypes}
        for aa in sequence:
            if aa in composition:
                composition[aa] = aa_counts[aa] / length * 100

        # Property-based composition
        hydrophobic_count = sum(1 for aa in sequence if aa in AA_PROPERTIES['hydrophobic'])
        polar_count = sum(1 for aa in sequence if aa in AA_PROPERTIES['polar'])
        positive_count = sum(1 for aa in sequence if aa in AA_PROPERTIES['positive'])
        negative_count = sum(1 for aa in sequence if aa in AA_PROPERTIES['negative'])
        special_count = sum(1 for aa in sequence if aa in AA_PROPERTIES['special'])

        composition_data.append({
            'sequence_id': seq_id,
            'sequence': sequence,
            'length': length,
            'hydrophobic_percent': hydrophobic_count / length * 100,
            'polar_percent': polar_count / length * 100,
            'positive_percent': positive_count / length * 100,
            'negative_percent': negative_count / length * 100,
            'special_percent': special_count / length * 100,
            **composition
        })

    return pd.DataFrame(composition_data)

def calculate_physicochemical_properties(sequences):
    """
    Calculate physicochemical properties of peptides

    Args:
        sequences (dict): Dictionary of sequence_id -> sequence

    Returns:
        pd.DataFrame: Property analysis
    """
    print("Calculating physicochemical properties...")

    properties_data = []

    for seq_id, sequence in sequences.items():
        sequence = sequence.upper()

        # Molecular weight
        mw = sum(AA_PROPERTIES['molecular_weight'].get(aa, 0) for aa in sequence)

        # Hydrophobicity (average)
        hydrophobicity = np.mean([AA_PROPERTIES['hydrophobicity'].get(aa, 0) for aa in sequence])

        # Net charge (at pH 7)
        net_charge = sum(1 for aa in sequence if aa in AA_PROPERTIES['positive']) - \
                    sum(1 for aa in sequence if aa in AA_PROPERTIES['negative'])

        # Cyclization potential (presence of Cys)
        cys_count = sequence.count('C')
        disulfide_potential = cys_count >= 2

        # Flexibility (Pro and Gly content)
        flexibility = (sequence.count('P') + sequence.count('G')) / len(sequence)

        # Aromaticity (Phe, Trp, Tyr content)
        aromatic_count = sequence.count('F') + sequence.count('W') + sequence.count('Y')
        aromaticity = aromatic_count / len(sequence)

        properties_data.append({
            'sequence_id': seq_id,
            'molecular_weight': mw,
            'hydrophobicity': hydrophobicity,
            'net_charge': net_charge,
            'cysteine_count': cys_count,
            'disulfide_potential': disulfide_potential,
            'flexibility': flexibility,
            'aromaticity': aromaticity,
            'length': len(sequence)
        })

    return pd.DataFrame(properties_data)

def assess_druggability(properties_df):
    """
    Assess drug-like properties of peptides

    Args:
        properties_df (pd.DataFrame): Physicochemical properties

    Returns:
        pd.DataFrame: Druggability assessment
    """
    print("Assessing drug-like properties...")

    druggability = properties_df.copy()

    # Rule of 5-like criteria for peptides (adapted for cyclic peptides)
    druggability['mw_acceptable'] = (druggability['molecular_weight'] <= 2000)  # Larger limit for peptides
    druggability['charge_acceptable'] = (abs(druggability['net_charge']) <= 3)
    druggability['hydrophobicity_acceptable'] = (
        (druggability['hydrophobicity'] >= -2.0) &
        (druggability['hydrophobicity'] <= 2.0)
    )

    # Cyclic peptide specific criteria
    druggability['cyclizable'] = druggability['disulfide_potential'] | (druggability['length'] <= 12)
    druggability['cell_penetration_potential'] = (
        (druggability['net_charge'] >= 2) |  # Positive charge
        (druggability['aromaticity'] >= 0.2)  # Aromatic residues
    )

    # Overall druggability score
    druggability['druggability_score'] = (
        druggability['mw_acceptable'].astype(int) +
        druggability['charge_acceptable'].astype(int) +
        druggability['hydrophobicity_acceptable'].astype(int) +
        druggability['cyclizable'].astype(int) +
        druggability['cell_penetration_potential'].astype(int)
    ) / 5.0

    return druggability

def create_visualizations(composition_df, properties_df, druggability_df, output_dir):
    """
    Create analysis visualizations

    Args:
        composition_df: Sequence composition data
        properties_df: Physicochemical properties
        druggability_df: Druggability assessment
        output_dir: Output directory
    """
    print("Creating visualizations...")

    os.makedirs(output_dir, exist_ok=True)

    # Set style
    plt.style.use('default')
    sns.set_palette("husl")

    # 1. Sequence length distribution
    plt.figure(figsize=(10, 6))
    plt.hist(composition_df['length'], bins=range(1, max(composition_df['length'])+2), alpha=0.7)
    plt.xlabel('Sequence Length')
    plt.ylabel('Number of Peptides')
    plt.title('Distribution of Peptide Lengths')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'length_distribution.png'), dpi=300, bbox_inches='tight')
    plt.close()

    # 2. Amino acid composition heatmap
    plt.figure(figsize=(12, 8))
    aa_cols = [col for col in composition_df.columns if col in restypes]
    composition_matrix = composition_df[aa_cols]

    if len(composition_matrix) > 1:
        sns.heatmap(composition_matrix.T, annot=True, fmt='.1f', cmap='YlOrRd',
                   xticklabels=composition_df['sequence_id'],
                   yticklabels=aa_cols)
    plt.title('Amino Acid Composition (%)')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'composition_heatmap.png'), dpi=300, bbox_inches='tight')
    plt.close()

    # 3. Property distributions
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))

    # Molecular weight
    axes[0,0].hist(properties_df['molecular_weight'], alpha=0.7, bins=10)
    axes[0,0].set_xlabel('Molecular Weight (Da)')
    axes[0,0].set_ylabel('Count')
    axes[0,0].set_title('Molecular Weight Distribution')
    axes[0,0].grid(True, alpha=0.3)

    # Hydrophobicity
    axes[0,1].hist(properties_df['hydrophobicity'], alpha=0.7, bins=10)
    axes[0,1].set_xlabel('Hydrophobicity (Kyte-Doolittle)')
    axes[0,1].set_ylabel('Count')
    axes[0,1].set_title('Hydrophobicity Distribution')
    axes[0,1].grid(True, alpha=0.3)

    # Net charge
    axes[1,0].hist(properties_df['net_charge'], alpha=0.7, bins=10)
    axes[1,0].set_xlabel('Net Charge')
    axes[1,0].set_ylabel('Count')
    axes[1,0].set_title('Net Charge Distribution')
    axes[1,0].grid(True, alpha=0.3)

    # Druggability score
    axes[1,1].hist(druggability_df['druggability_score'], alpha=0.7, bins=10)
    axes[1,1].set_xlabel('Druggability Score')
    axes[1,1].set_ylabel('Count')
    axes[1,1].set_title('Druggability Score Distribution')
    axes[1,1].grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'property_distributions.png'), dpi=300, bbox_inches='tight')
    plt.close()

    # 4. Property correlations
    if len(properties_df) > 2:
        plt.figure(figsize=(10, 8))
        numeric_cols = ['molecular_weight', 'hydrophobicity', 'net_charge', 'flexibility', 'aromaticity']
        corr_matrix = properties_df[numeric_cols].corr()
        sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', center=0)
        plt.title('Property Correlations')
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'property_correlations.png'), dpi=300, bbox_inches='tight')
        plt.close()

    print(f"  Visualizations saved to: {output_dir}")

def main():
    parser = argparse.ArgumentParser(description="Analyze cyclic peptide sequences and properties")
    parser.add_argument('--sequences', type=str,
                       help='Path to FASTA file containing peptide sequences')
    parser.add_argument('--sequence', type=str,
                       help='Single peptide sequence to analyze')
    parser.add_argument('--output', type=str, default='examples/peptide_analysis/',
                       help='Output directory for analysis results')
    parser.add_argument('--create_demo', action='store_true',
                       help='Create demo sequences for analysis')

    args = parser.parse_args()

    print("=" * 60)
    print("PepFlowww Peptide Sequence Analysis")
    print("=" * 60)

    # Get sequences
    sequences = {}

    if args.create_demo or (not args.sequences and not args.sequence):
        sequences = create_demo_sequences()

    if args.sequences:
        if os.path.exists(args.sequences):
            file_sequences = read_sequences_from_fasta(args.sequences)
            sequences.update(file_sequences)
            print(f"Loaded {len(file_sequences)} sequences from {args.sequences}")
        else:
            print(f"FASTA file not found: {args.sequences}")

    if args.sequence:
        sequences['input_sequence'] = args.sequence.upper()
        print(f"Added input sequence: {args.sequence}")

    if not sequences:
        print("No sequences provided. Use --create_demo to generate demo sequences.")
        return

    print(f"Total sequences to analyze: {len(sequences)}")

    # Create output directory
    os.makedirs(args.output, exist_ok=True)

    # Run analyses
    print("\n" + "=" * 40)

    # 1. Composition analysis
    composition_df = analyze_sequence_composition(sequences)
    composition_output = os.path.join(args.output, 'composition_analysis.csv')
    composition_df.to_csv(composition_output, index=False)
    print(f"  Composition analysis saved: {composition_output}")

    # 2. Physicochemical properties
    properties_df = calculate_physicochemical_properties(sequences)
    properties_output = os.path.join(args.output, 'physicochemical_properties.csv')
    properties_df.to_csv(properties_output, index=False)
    print(f"  Properties analysis saved: {properties_output}")

    # 3. Druggability assessment
    druggability_df = assess_druggability(properties_df)
    druggability_output = os.path.join(args.output, 'druggability_assessment.csv')
    druggability_df.to_csv(druggability_output, index=False)
    print(f"  Druggability assessment saved: {druggability_output}")

    # 4. Create visualizations
    vis_dir = os.path.join(args.output, 'visualizations')
    create_visualizations(composition_df, properties_df, druggability_df, vis_dir)

    # 5. Summary report
    summary_output = os.path.join(args.output, 'analysis_summary.txt')
    with open(summary_output, 'w') as f:
        f.write("Peptide Sequence Analysis Summary\n")
        f.write("=================================\n\n")

        f.write(f"Total sequences analyzed: {len(sequences)}\n")
        f.write(f"Average length: {composition_df['length'].mean():.1f} ± {composition_df['length'].std():.1f}\n")
        f.write(f"Length range: {composition_df['length'].min()} - {composition_df['length'].max()}\n\n")

        f.write("Physicochemical Properties (Average):\n")
        f.write(f"  Molecular weight: {properties_df['molecular_weight'].mean():.1f} ± {properties_df['molecular_weight'].std():.1f} Da\n")
        f.write(f"  Hydrophobicity: {properties_df['hydrophobicity'].mean():.2f} ± {properties_df['hydrophobicity'].std():.2f}\n")
        f.write(f"  Net charge: {properties_df['net_charge'].mean():.1f} ± {properties_df['net_charge'].std():.1f}\n")
        f.write(f"  Flexibility: {properties_df['flexibility'].mean():.2f} ± {properties_df['flexibility'].std():.2f}\n")
        f.write(f"  Aromaticity: {properties_df['aromaticity'].mean():.2f} ± {properties_df['aromaticity'].std():.2f}\n\n")

        f.write("Druggability Assessment:\n")
        f.write(f"  Average druggability score: {druggability_df['druggability_score'].mean():.2f}\n")
        f.write(f"  Peptides with high druggability (>0.6): {sum(druggability_df['druggability_score'] > 0.6)}/{len(druggability_df)}\n")
        f.write(f"  Cyclizable peptides: {sum(druggability_df['cyclizable'])}/{len(druggability_df)}\n")
        f.write(f"  Cell penetration potential: {sum(druggability_df['cell_penetration_potential'])}/{len(druggability_df)}\n\n")

        f.write("Top 3 sequences by druggability score:\n")
        top_sequences = druggability_df.nlargest(3, 'druggability_score')
        for _, row in top_sequences.iterrows():
            seq_id = row['sequence_id']
            score = row['druggability_score']
            sequence = sequences[seq_id]
            f.write(f"  {seq_id}: {sequence} (score: {score:.2f})\n")

    print(f"  Summary report saved: {summary_output}")

    print("\n" + "=" * 60)
    print("ANALYSIS COMPLETE")
    print("=" * 60)
    print(f"Results saved to: {args.output}")
    print("\nFiles created:")
    for file in os.listdir(args.output):
        if os.path.isfile(os.path.join(args.output, file)):
            print(f"  {file}")

    print("\nVisualization files:")
    if os.path.exists(vis_dir):
        for file in os.listdir(vis_dir):
            print(f"  visualizations/{file}")

    print(f"\nAnalyzed {len(sequences)} peptide sequences")
    print(f"Average length: {composition_df['length'].mean():.1f} residues")
    print(f"Average druggability score: {druggability_df['druggability_score'].mean():.2f}/1.0")

if __name__ == '__main__':
    main()