#!/usr/bin/env python3
"""
Script: analyze_peptides.py
Description: Analyze cyclic peptide sequences and calculate physicochemical properties

Original Use Case: examples/use_case_5_peptide_analysis.py
Dependencies Removed: repo/PepFlowww/data/residue_constants (inlined)

Usage:
    python scripts/analyze_peptides.py --input <input_file> --output <output_file>

Example:
    python scripts/analyze_peptides.py --input examples/data/sequences/demo_peptides.fasta --output results/analysis.csv
"""

# ==============================================================================
# Minimal Imports (only essential packages)
# ==============================================================================
import argparse
from pathlib import Path
from typing import Union, Optional, Dict, Any, List
import json
from collections import Counter

# Essential scientific packages
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# ==============================================================================
# Configuration (extracted from use case)
# ==============================================================================
DEFAULT_CONFIG = {
    "include_visualizations": True,
    "include_druggability": True,
    "include_composition": True,
    "output_format": "csv",
    "plot_dpi": 300,
    "plot_style": "default"
}

# ==============================================================================
# Inlined Constants (from repo/PepFlowww/data/residue_constants.py)
# ==============================================================================
AMINO_ACIDS = [
    "A", "R", "N", "D", "C", "Q", "E", "G", "H", "I",
    "L", "K", "M", "F", "P", "S", "T", "W", "Y", "V"
]

AMINO_ACID_ORDER = {aa: i for i, aa in enumerate(AMINO_ACIDS)}

# ==============================================================================
# Inlined Amino Acid Properties (simplified from use case)
# ==============================================================================
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

# ==============================================================================
# Inlined Utility Functions (simplified from use case)
# ==============================================================================
def parse_fasta(fasta_path: Path) -> Dict[str, str]:
    """Parse FASTA file to extract sequences. Simplified from use case."""
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

def validate_sequence(sequence: str) -> bool:
    """Validate that sequence contains only valid amino acids."""
    sequence = sequence.upper()
    return all(aa in AMINO_ACIDS for aa in sequence)

def create_demo_sequences() -> Dict[str, str]:
    """Create demo peptide sequences for testing."""
    return {
        'cyclic_peptide_1': 'CYCLIGKRC',
        'cyclic_peptide_2': 'ACDEFGHIK',
        'cyclic_peptide_3': 'RVTWYKLPC',
        'cyclic_peptide_4': 'GFPSWQNMC',
        'cyclic_peptide_5': 'ALTDHENVC',
        'linear_control': 'GPGPGPGPGP',
        'antimicrobial': 'RRWWRFKKLR',
        'cell_penetrating': 'RRRQRRKKRG'
    }

def save_results(results: Dict[str, pd.DataFrame], output_file: Path) -> None:
    """Save analysis results to files."""
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Save each dataframe
    for name, df in results.items():
        if name == 'visualizations':
            continue  # Skip non-dataframe results

        file_path = output_file.parent / f"{output_file.stem}_{name}.csv"
        df.to_csv(file_path, index=False)
        print(f"Saved {name}: {file_path}")

# ==============================================================================
# Core Functions (extracted and simplified from use case)
# ==============================================================================
def analyze_composition(sequences: Dict[str, str]) -> pd.DataFrame:
    """Analyze amino acid composition of sequences."""
    print("Analyzing sequence composition...")

    composition_data = []

    for seq_id, sequence in sequences.items():
        sequence = sequence.upper()

        # Validate sequence
        if not validate_sequence(sequence):
            print(f"Warning: Invalid amino acids in {seq_id}, skipping...")
            continue

        length = len(sequence)

        # Count amino acids
        aa_counts = Counter(sequence)

        # Calculate percentages for each amino acid
        composition = {aa: 0.0 for aa in AMINO_ACIDS}
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

def calculate_properties(sequences: Dict[str, str]) -> pd.DataFrame:
    """Calculate physicochemical properties of peptides."""
    print("Calculating physicochemical properties...")

    properties_data = []

    for seq_id, sequence in sequences.items():
        sequence = sequence.upper()

        # Validate sequence
        if not validate_sequence(sequence):
            continue

        # Molecular weight
        mw = sum(AA_PROPERTIES['molecular_weight'].get(aa, 0) for aa in sequence)

        # Hydrophobicity (average)
        hydrophobicity = np.mean([AA_PROPERTIES['hydrophobicity'].get(aa, 0) for aa in sequence])

        # Net charge (at pH 7)
        net_charge = (sum(1 for aa in sequence if aa in AA_PROPERTIES['positive']) -
                      sum(1 for aa in sequence if aa in AA_PROPERTIES['negative']))

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

def assess_druggability(properties_df: pd.DataFrame) -> pd.DataFrame:
    """Assess drug-like properties of peptides."""
    print("Assessing drug-like properties...")

    druggability = properties_df.copy()

    # Rule of 5-like criteria adapted for cyclic peptides
    druggability['mw_acceptable'] = (druggability['molecular_weight'] <= 2000)
    druggability['charge_acceptable'] = (abs(druggability['net_charge']) <= 3)
    druggability['hydrophobicity_acceptable'] = (
        (druggability['hydrophobicity'] >= -2.0) &
        (druggability['hydrophobicity'] <= 2.0)
    )

    # Cyclic peptide specific criteria
    druggability['cyclizable'] = druggability['disulfide_potential'] | (druggability['length'] <= 12)
    druggability['cell_penetration_potential'] = (
        (druggability['net_charge'] >= 2) |
        (druggability['aromaticity'] >= 0.2)
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

def create_visualizations(
    composition_df: pd.DataFrame,
    properties_df: pd.DataFrame,
    druggability_df: pd.DataFrame,
    output_dir: Path,
    config: Dict[str, Any]
) -> None:
    """Create analysis visualizations with minimal matplotlib."""
    print("Creating visualizations...")

    output_dir.mkdir(parents=True, exist_ok=True)

    # Set basic style
    plt.style.use(config.get('plot_style', 'default'))

    # 1. Sequence length distribution
    plt.figure(figsize=(10, 6))
    plt.hist(composition_df['length'], bins=range(1, max(composition_df['length'])+2), alpha=0.7)
    plt.xlabel('Sequence Length')
    plt.ylabel('Number of Peptides')
    plt.title('Distribution of Peptide Lengths')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_dir / 'length_distribution.png', dpi=config.get('plot_dpi', 300), bbox_inches='tight')
    plt.close()

    # 2. Property distributions
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))

    # Molecular weight
    axes[0,0].hist(properties_df['molecular_weight'], alpha=0.7, bins=10)
    axes[0,0].set_xlabel('Molecular Weight (Da)')
    axes[0,0].set_ylabel('Count')
    axes[0,0].set_title('Molecular Weight Distribution')
    axes[0,0].grid(True, alpha=0.3)

    # Hydrophobicity
    axes[0,1].hist(properties_df['hydrophobicity'], alpha=0.7, bins=10)
    axes[0,1].set_xlabel('Hydrophobicity')
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
    plt.savefig(output_dir / 'property_distributions.png', dpi=config.get('plot_dpi', 300), bbox_inches='tight')
    plt.close()

    print(f"Visualizations saved to: {output_dir}")

# ==============================================================================
# Core Function (main logic extracted from use case)
# ==============================================================================
def run_analyze_peptides(
    input_file: Union[str, Path, None] = None,
    output_file: Optional[Union[str, Path]] = None,
    sequence: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Main function for peptide sequence analysis.

    Args:
        input_file: Path to input FASTA file (optional)
        output_file: Path to save output (optional)
        sequence: Single sequence to analyze (optional)
        config: Configuration dict (uses DEFAULT_CONFIG if not provided)
        **kwargs: Override specific config parameters

    Returns:
        Dict containing:
            - composition: Composition analysis dataframe
            - properties: Properties analysis dataframe
            - druggability: Druggability assessment dataframe
            - output_files: List of output file paths
            - metadata: Execution metadata

    Example:
        >>> result = run_analyze_peptides("input.fasta", "output")
        >>> print(result['output_files'])
    """
    # Setup
    config = {**DEFAULT_CONFIG, **(config or {}), **kwargs}

    # Load sequences
    sequences = {}

    if input_file:
        input_file = Path(input_file)
        if input_file.exists():
            sequences.update(parse_fasta(input_file))
        else:
            print(f"Warning: Input file not found: {input_file}")

    if sequence:
        sequences['input_sequence'] = sequence.upper()

    if not sequences:
        print("No input provided, creating demo sequences...")
        sequences = create_demo_sequences()

    print(f"Analyzing {len(sequences)} sequences...")

    # Core processing
    composition_df = analyze_composition(sequences)
    properties_df = calculate_properties(sequences)

    results = {
        'composition': composition_df,
        'properties': properties_df
    }

    if config.get('include_druggability', True):
        druggability_df = assess_druggability(properties_df)
        results['druggability'] = druggability_df
    else:
        druggability_df = None

    # Save outputs
    output_files = []
    if output_file:
        output_file = Path(output_file)
        save_results(results, output_file)

        # Create visualizations if requested
        if config.get('include_visualizations', True):
            vis_dir = output_file.parent / 'visualizations'
            create_visualizations(composition_df, properties_df, druggability_df, vis_dir, config)
            output_files.extend([str(f) for f in vis_dir.glob('*.png')])

        output_files.extend([str(f) for f in output_file.parent.glob(f"{output_file.stem}_*.csv")])

    return {
        "composition": composition_df,
        "properties": properties_df,
        "druggability": druggability_df,
        "output_files": output_files,
        "metadata": {
            "input_file": str(input_file) if input_file else None,
            "sequence_count": len(sequences),
            "config": config
        }
    }

# ==============================================================================
# CLI Interface
# ==============================================================================
def main():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('--input', '-i', help='Input FASTA file path')
    parser.add_argument('--output', '-o', help='Output file prefix')
    parser.add_argument('--sequence', '-s', help='Single peptide sequence to analyze')
    parser.add_argument('--config', '-c', help='Config file (JSON)')
    parser.add_argument('--demo', action='store_true', help='Use demo sequences')
    parser.add_argument('--no-viz', action='store_true', help='Skip visualizations')
    parser.add_argument('--no-drug', action='store_true', help='Skip druggability assessment')

    args = parser.parse_args()

    # Load config if provided
    config = DEFAULT_CONFIG.copy()
    if args.config:
        with open(args.config) as f:
            config.update(json.load(f))

    # Override config with command line arguments
    if args.no_viz:
        config['include_visualizations'] = False
    if args.no_drug:
        config['include_druggability'] = False

    # Determine input
    input_file = args.input
    sequence = args.sequence
    if args.demo:
        input_file = None  # Will trigger demo sequence creation
        sequence = None

    # Run analysis
    result = run_analyze_peptides(
        input_file=input_file,
        output_file=args.output,
        sequence=sequence,
        config=config
    )

    # Print summary
    metadata = result['metadata']
    print(f"\nAnalysis complete!")
    print(f"Sequences analyzed: {metadata['sequence_count']}")

    if result['output_files']:
        print(f"Output files: {len(result['output_files'])}")
        for file_path in result['output_files']:
            print(f"  {file_path}")

    # Show key statistics
    if not result['properties'].empty:
        props = result['properties']
        print(f"\nKey Statistics:")
        print(f"  Average length: {props['length'].mean():.1f} residues")
        print(f"  Average MW: {props['molecular_weight'].mean():.1f} Da")
        print(f"  Average hydrophobicity: {props['hydrophobicity'].mean():.2f}")

        if result['druggability'] is not None:
            drug_score = result['druggability']['druggability_score'].mean()
            print(f"  Average druggability: {drug_score:.2f}/1.0")

    return result

if __name__ == '__main__':
    main()