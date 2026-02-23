"""
Utility functions for peptide analysis and manipulation.

Common functions extracted from use case scripts.
"""

import random
from typing import Dict, List, Any, Optional
from collections import Counter
import numpy as np

from .constants import AA_PROPERTIES, AA_GROUPS, AMINO_ACIDS


def calculate_basic_properties(sequence: str) -> Dict[str, Any]:
    """
    Calculate basic physicochemical properties of a peptide sequence.

    Extracted from use case 5 (peptide analysis).

    Args:
        sequence: Peptide sequence

    Returns:
        dict: Calculated properties
    """
    sequence = sequence.upper()
    length = len(sequence)

    if length == 0:
        return {}

    # Molecular weight
    mw = sum(AA_PROPERTIES['molecular_weight'].get(aa, 0) for aa in sequence)

    # Hydrophobicity (average Kyte-Doolittle scale)
    hydrophobicity = np.mean([
        AA_PROPERTIES['hydrophobicity'].get(aa, 0) for aa in sequence
    ])

    # Net charge at pH 7
    net_charge = sum(AA_PROPERTIES['charge_ph7'].get(aa, 0) for aa in sequence)

    # Composition analysis
    composition = {group: sum(1 for aa in sequence if aa in aas)
                   for group, aas in AA_GROUPS.items()}

    # Ratios
    hydrophobic_ratio = composition['hydrophobic'] / length
    polar_ratio = composition['polar'] / length
    charged_ratio = (composition['positive'] + composition['negative']) / length

    # Special features
    cys_count = sequence.count('C')
    disulfide_potential = cys_count >= 2 and cys_count % 2 == 0

    # Flexibility (Pro and Gly content)
    flexibility = (sequence.count('P') + sequence.count('G')) / length

    # Aromaticity (Phe, Trp, Tyr content)
    aromatic_count = sequence.count('F') + sequence.count('W') + sequence.count('Y')
    aromaticity = aromatic_count / length

    return {
        'length': length,
        'molecular_weight': mw,
        'hydrophobicity': hydrophobicity,
        'net_charge': net_charge,
        'hydrophobic_ratio': hydrophobic_ratio,
        'polar_ratio': polar_ratio,
        'charged_ratio': charged_ratio,
        'cysteine_count': cys_count,
        'disulfide_potential': disulfide_potential,
        'flexibility': flexibility,
        'aromaticity': aromaticity,
        'unique_residues': len(set(sequence))
    }


def balance_charges(sequence: List[str], target_balance: float = 0.5) -> List[str]:
    """
    Balance charged residues in a sequence.

    Extracted from sequence generation logic.

    Args:
        sequence: List of amino acids
        target_balance: Target ratio of positive to negative charges

    Returns:
        list: Balanced sequence
    """
    sequence = sequence.copy()

    pos_count = sum(1 for aa in sequence if aa in AA_GROUPS['positive'])
    neg_count = sum(1 for aa in sequence if aa in AA_GROUPS['negative'])

    total_charged = pos_count + neg_count
    if total_charged == 0:
        return sequence

    current_ratio = pos_count / total_charged if total_charged > 0 else 0.5

    # If already balanced, return as-is
    if abs(current_ratio - target_balance) < 0.2:
        return sequence

    # Find non-charged residues to replace
    neutral_positions = [
        i for i, aa in enumerate(sequence)
        if aa not in AA_GROUPS['positive'] + AA_GROUPS['negative']
    ]

    if not neutral_positions:
        return sequence

    # Determine what to add
    if current_ratio < target_balance:
        # Need more positive charges
        replace_with = AA_GROUPS['positive']
    else:
        # Need more negative charges
        replace_with = AA_GROUPS['negative']

    # Replace a few residues
    num_replace = min(len(neutral_positions), abs(pos_count - neg_count) // 2 + 1)
    positions_to_replace = random.sample(neutral_positions, num_replace)

    for pos in positions_to_replace:
        sequence[pos] = random.choice(replace_with)

    return sequence


def analyze_sequence_diversity(sequences: List[str]) -> Dict[str, Any]:
    """
    Analyze diversity within a set of sequences.

    Args:
        sequences: List of peptide sequences

    Returns:
        dict: Diversity metrics
    """
    if not sequences:
        return {}

    lengths = [len(seq) for seq in sequences]
    all_sequences = set(sequences)

    # Amino acid usage
    all_aas = ''.join(sequences)
    aa_counts = Counter(all_aas)
    aa_diversity = len(aa_counts) / len(AMINO_ACIDS)  # Shannon-like diversity

    # Position-specific diversity (for sequences of similar length)
    modal_length = max(set(lengths), key=lengths.count)
    similar_length_seqs = [seq for seq in sequences if len(seq) == modal_length]

    position_diversity = 0
    if len(similar_length_seqs) > 1:
        position_entropies = []
        for pos in range(modal_length):
            pos_aas = [seq[pos] for seq in similar_length_seqs]
            pos_counts = Counter(pos_aas)
            # Calculate Shannon entropy
            total = len(pos_aas)
            entropy = -sum((count/total) * np.log2(count/total)
                          for count in pos_counts.values())
            position_entropies.append(entropy)
        position_diversity = np.mean(position_entropies) / np.log2(len(AMINO_ACIDS))

    return {
        'total_sequences': len(sequences),
        'unique_sequences': len(all_sequences),
        'uniqueness_ratio': len(all_sequences) / len(sequences),
        'length_diversity': {
            'min': min(lengths),
            'max': max(lengths),
            'mean': np.mean(lengths),
            'std': np.std(lengths)
        },
        'aa_diversity': aa_diversity,
        'position_diversity': position_diversity,
        'aa_usage': dict(aa_counts)
    }


def create_sequence_summary(sequences: Dict[str, str]) -> Dict[str, Any]:
    """
    Create a summary of sequence collection.

    Args:
        sequences: Dict of sequence_id -> sequence

    Returns:
        dict: Summary statistics
    """
    if not sequences:
        return {'count': 0}

    sequence_list = list(sequences.values())
    properties = [calculate_basic_properties(seq) for seq in sequence_list]

    # Aggregate statistics
    summary = {
        'count': len(sequences),
        'avg_length': np.mean([p['length'] for p in properties]),
        'avg_molecular_weight': np.mean([p['molecular_weight'] for p in properties]),
        'avg_hydrophobicity': np.mean([p['hydrophobicity'] for p in properties]),
        'avg_net_charge': np.mean([p['net_charge'] for p in properties]),
        'avg_flexibility': np.mean([p['flexibility'] for p in properties]),
        'disulfide_capable': sum(1 for p in properties if p['disulfide_potential']),
    }

    # Add diversity metrics
    summary.update(analyze_sequence_diversity(sequence_list))

    return summary


def generate_random_sequence(
    length: int,
    amino_acid_weights: Optional[Dict[str, float]] = None
) -> str:
    """
    Generate a random peptide sequence.

    Args:
        length: Sequence length
        amino_acid_weights: Optional weights for amino acids

    Returns:
        str: Generated sequence
    """
    if amino_acid_weights:
        aas = list(amino_acid_weights.keys())
        weights = list(amino_acid_weights.values())
        sequence = random.choices(aas, weights=weights, k=length)
    else:
        sequence = random.choices(AMINO_ACIDS, k=length)

    return ''.join(sequence)


def mutate_sequence(
    sequence: str,
    mutation_rate: float = 0.1,
    preserve_cysteines: bool = True
) -> str:
    """
    Randomly mutate a sequence.

    Args:
        sequence: Original sequence
        mutation_rate: Probability of mutation per position
        preserve_cysteines: If True, don't mutate cysteines

    Returns:
        str: Mutated sequence
    """
    sequence = list(sequence.upper())

    for i, aa in enumerate(sequence):
        if random.random() < mutation_rate:
            if preserve_cysteines and aa == 'C':
                continue

            # Choose a different amino acid
            available_aas = [new_aa for new_aa in AMINO_ACIDS if new_aa != aa]
            sequence[i] = random.choice(available_aas)

    return ''.join(sequence)