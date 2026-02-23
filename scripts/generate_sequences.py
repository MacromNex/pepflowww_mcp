#!/usr/bin/env python3
"""
Script: generate_sequences.py
Description: Generate cyclic peptide sequences using simplified sampling methods

Original Use Case: examples/use_case_2_sample_peptides.py
Dependencies Removed: FlowModel, complex sampling pipeline (simplified to statistical generation)

Usage:
    python scripts/generate_sequences.py --num_samples 10 --output <output_file>

Example:
    python scripts/generate_sequences.py --num_samples 8 --output results/generated_sequences.fasta
"""

# ==============================================================================
# Minimal Imports (only essential packages)
# ==============================================================================
import argparse
from pathlib import Path
from typing import Union, Optional, Dict, Any, List
import json
import random

# Essential scientific packages
import numpy as np
import pandas as pd

# ==============================================================================
# Configuration (extracted from use case)
# ==============================================================================
DEFAULT_CONFIG = {
    "sequence_length_range": [6, 15],
    "amino_acid_weights": "uniform",
    "include_cysteines": True,
    "cysteine_probability": 0.15,
    "hydrophobic_bias": 0.3,
    "charged_balance": True,
    "output_format": "fasta",
    "add_metadata": True
}

# ==============================================================================
# Inlined Constants (simplified from repo)
# ==============================================================================
AMINO_ACIDS = [
    "A", "R", "N", "D", "C", "Q", "E", "G", "H", "I",
    "L", "K", "M", "F", "P", "S", "T", "W", "Y", "V"
]

# Amino acid property groups for biased sampling
AA_GROUPS = {
    'hydrophobic': ['A', 'V', 'I', 'L', 'M', 'F', 'W', 'Y'],
    'polar': ['S', 'T', 'N', 'Q'],
    'positive': ['K', 'R', 'H'],
    'negative': ['D', 'E'],
    'special': ['C', 'P', 'G']
}

# Frequency weights based on natural peptides (approximate)
NATURAL_FREQUENCIES = {
    'A': 0.074, 'R': 0.042, 'N': 0.044, 'D': 0.059, 'C': 0.033,
    'Q': 0.037, 'E': 0.058, 'G': 0.074, 'H': 0.029, 'I': 0.053,
    'L': 0.093, 'K': 0.059, 'M': 0.025, 'F': 0.045, 'P': 0.039,
    'S': 0.067, 'T': 0.068, 'W': 0.013, 'Y': 0.033, 'V': 0.068
}

# ==============================================================================
# Inlined Utility Functions
# ==============================================================================
def validate_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and normalize configuration parameters."""
    validated = config.copy()

    # Ensure sequence length range is valid
    length_range = validated.get('sequence_length_range', [6, 15])
    if length_range[0] > length_range[1] or length_range[0] < 1:
        print("Warning: Invalid sequence length range, using default [6, 15]")
        validated['sequence_length_range'] = [6, 15]

    return validated

def save_sequences_fasta(sequences: List[Dict[str, str]], output_file: Path) -> None:
    """Save sequences to FASTA format."""
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w') as f:
        for seq_data in sequences:
            f.write(f">{seq_data['id']}\n{seq_data['sequence']}\n")

    print(f"Saved {len(sequences)} sequences to {output_file}")

def save_sequences_csv(sequences: List[Dict[str, str]], output_file: Path) -> None:
    """Save sequences to CSV format with metadata."""
    output_file.parent.mkdir(parents=True, exist_ok=True)

    df = pd.DataFrame(sequences)
    df.to_csv(output_file, index=False)

    print(f"Saved {len(sequences)} sequences to {output_file}")

# ==============================================================================
# Core Sequence Generation Functions
# ==============================================================================
def sample_amino_acid(weights: str = "uniform", exclude: Optional[List[str]] = None) -> str:
    """Sample a single amino acid based on specified weighting scheme."""
    available_aas = [aa for aa in AMINO_ACIDS if aa not in (exclude or [])]

    if weights == "uniform":
        return random.choice(available_aas)
    elif weights == "natural":
        # Use natural frequency weights
        weights_list = [NATURAL_FREQUENCIES.get(aa, 0.05) for aa in available_aas]
        return random.choices(available_aas, weights=weights_list)[0]
    elif weights == "hydrophobic_bias":
        # Bias towards hydrophobic residues for membrane-targeting peptides
        weights_list = []
        for aa in available_aas:
            if aa in AA_GROUPS['hydrophobic']:
                weights_list.append(0.4)
            elif aa in AA_GROUPS['polar']:
                weights_list.append(0.3)
            else:
                weights_list.append(0.2)
        return random.choices(available_aas, weights=weights_list)[0]
    else:
        return random.choice(available_aas)

def balance_charges(sequence: List[str], config: Dict[str, Any]) -> List[str]:
    """Balance charged residues in the sequence if configured."""
    if not config.get('charged_balance', False):
        return sequence

    pos_count = sum(1 for aa in sequence if aa in AA_GROUPS['positive'])
    neg_count = sum(1 for aa in sequence if aa in AA_GROUPS['negative'])

    # If highly imbalanced, replace some residues
    if abs(pos_count - neg_count) > len(sequence) // 2:
        # Find non-charged residues to replace
        neutral_positions = [i for i, aa in enumerate(sequence)
                           if aa not in AA_GROUPS['positive'] + AA_GROUPS['negative']]

        if neutral_positions:
            # Balance by adding opposite charges
            if pos_count > neg_count:
                # Add negative charges
                replace_with = AA_GROUPS['negative']
            else:
                # Add positive charges
                replace_with = AA_GROUPS['positive']

            # Replace a few neutral residues
            num_replace = min(len(neutral_positions), abs(pos_count - neg_count) // 2)
            positions_to_replace = random.sample(neutral_positions, num_replace)

            for pos in positions_to_replace:
                sequence[pos] = random.choice(replace_with)

    return sequence

def add_disulfide_bonds(sequence: List[str], config: Dict[str, Any]) -> List[str]:
    """Add cysteine residues for potential disulfide bonds if configured."""
    if not config.get('include_cysteines', True):
        return sequence

    cys_prob = config.get('cysteine_probability', 0.15)

    # Ensure we have even number of cysteines (for disulfide bonds)
    current_cys = sum(1 for aa in sequence if aa == 'C')

    # If we have an odd number, add one more or remove one
    if current_cys % 2 == 1:
        # Try to add one more
        non_cys_positions = [i for i, aa in enumerate(sequence) if aa != 'C']
        if non_cys_positions and random.random() < 0.7:
            pos = random.choice(non_cys_positions)
            sequence[pos] = 'C'
        elif current_cys > 0:
            # Remove one cysteine
            cys_positions = [i for i, aa in enumerate(sequence) if aa == 'C']
            if cys_positions:
                pos = random.choice(cys_positions)
                sequence[pos] = sample_amino_acid(config.get('amino_acid_weights', 'uniform'))

    return sequence

def generate_single_sequence(
    length: Optional[int] = None,
    config: Dict[str, Any] = None
) -> str:
    """Generate a single peptide sequence."""
    config = config or DEFAULT_CONFIG

    # Determine sequence length
    if length is None:
        min_len, max_len = config['sequence_length_range']
        length = random.randint(min_len, max_len)

    # Generate base sequence
    sequence = []
    for _ in range(length):
        aa = sample_amino_acid(
            weights=config.get('amino_acid_weights', 'uniform')
        )
        sequence.append(aa)

    # Apply post-processing
    sequence = balance_charges(sequence, config)
    sequence = add_disulfide_bonds(sequence, config)

    return ''.join(sequence)

def calculate_sequence_properties(sequence: str) -> Dict[str, Any]:
    """Calculate basic properties of a sequence."""
    length = len(sequence)

    # Count amino acid types
    composition = {group: sum(1 for aa in sequence if aa in aas)
                   for group, aas in AA_GROUPS.items()}

    # Calculate percentages
    percentages = {f"{group}_percent": count/length*100
                   for group, count in composition.items()}

    # Net charge (simplified)
    net_charge = composition['positive'] - composition['negative']

    # Hydrophobicity estimate
    hydrophobic_ratio = composition['hydrophobic'] / length

    return {
        'length': length,
        'net_charge': net_charge,
        'hydrophobic_ratio': hydrophobic_ratio,
        'cysteine_count': sequence.count('C'),
        **percentages
    }

# ==============================================================================
# Core Function (main logic)
# ==============================================================================
def run_generate_sequences(
    num_samples: int = 10,
    output_file: Optional[Union[str, Path]] = None,
    config: Optional[Dict[str, Any]] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Main function for generating cyclic peptide sequences.

    Args:
        num_samples: Number of sequences to generate
        output_file: Path to save output (optional)
        config: Configuration dict (uses DEFAULT_CONFIG if not provided)
        **kwargs: Override specific config parameters

    Returns:
        Dict containing:
            - sequences: List of generated sequences with metadata
            - output_file: Path to output file (if saved)
            - metadata: Generation metadata

    Example:
        >>> result = run_generate_sequences(10, "output.fasta")
        >>> print(len(result['sequences']))
    """
    # Setup
    config = {**DEFAULT_CONFIG, **(config or {}), **kwargs}
    config = validate_config(config)

    print(f"Generating {num_samples} sequences...")

    # Generate sequences
    sequences = []
    for i in range(num_samples):
        sequence = generate_single_sequence(config=config)
        properties = calculate_sequence_properties(sequence)

        seq_data = {
            'id': f'generated_peptide_{i:03d}',
            'sequence': sequence,
            **properties
        }

        # Add metadata if configured
        if config.get('add_metadata', True):
            seq_data.update({
                'generation_method': 'statistical_sampling',
                'config': json.dumps(config)
            })

        sequences.append(seq_data)

    # Save output if requested
    output_path = None
    if output_file:
        output_file = Path(output_file)
        output_path = output_file

        if config.get('output_format', 'fasta') == 'csv':
            save_sequences_csv(sequences, output_file)
        else:
            save_sequences_fasta(sequences, output_file)

    # Calculate summary statistics
    lengths = [seq['length'] for seq in sequences]
    charges = [seq['net_charge'] for seq in sequences]

    return {
        "sequences": sequences,
        "output_file": str(output_path) if output_path else None,
        "metadata": {
            "num_samples": num_samples,
            "avg_length": np.mean(lengths),
            "avg_charge": np.mean(charges),
            "length_range": [min(lengths), max(lengths)],
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
    parser.add_argument('--num_samples', '-n', type=int, default=10,
                       help='Number of sequences to generate')
    parser.add_argument('--output', '-o', help='Output file path')
    parser.add_argument('--config', '-c', help='Config file (JSON)')
    parser.add_argument('--length', '-l', type=int, help='Fixed sequence length')
    parser.add_argument('--format', choices=['fasta', 'csv'], default='fasta',
                       help='Output format')
    parser.add_argument('--weights', choices=['uniform', 'natural', 'hydrophobic_bias'],
                       default='uniform', help='Amino acid sampling weights')
    parser.add_argument('--no-balance', action='store_true',
                       help='Disable charge balancing')
    parser.add_argument('--no-cysteines', action='store_true',
                       help='Exclude cysteines')

    args = parser.parse_args()

    # Load config if provided
    config = DEFAULT_CONFIG.copy()
    if args.config:
        with open(args.config) as f:
            config.update(json.load(f))

    # Override config with command line arguments
    if args.format:
        config['output_format'] = args.format
    if args.weights:
        config['amino_acid_weights'] = args.weights
    if args.no_balance:
        config['charged_balance'] = False
    if args.no_cysteines:
        config['include_cysteines'] = False
    if args.length:
        config['sequence_length_range'] = [args.length, args.length]

    # Generate sequences
    result = run_generate_sequences(
        num_samples=args.num_samples,
        output_file=args.output,
        config=config
    )

    # Print summary
    metadata = result['metadata']
    print(f"\nGeneration complete!")
    print(f"Generated {metadata['num_samples']} sequences")
    print(f"Average length: {metadata['avg_length']:.1f} residues")
    print(f"Average charge: {metadata['avg_charge']:.1f}")
    print(f"Length range: {metadata['length_range'][0]}-{metadata['length_range'][1]}")

    if result['output_file']:
        print(f"Saved to: {result['output_file']}")

    # Show some example sequences
    print(f"\nExample sequences:")
    for i, seq in enumerate(result['sequences'][:3]):
        print(f"  {seq['id']}: {seq['sequence']} (len={seq['length']}, charge={seq['net_charge']})")

    return result

if __name__ == '__main__':
    main()