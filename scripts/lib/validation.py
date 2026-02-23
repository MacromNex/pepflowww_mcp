"""
Validation utilities for peptide sequences and configurations.

Extracted validation logic from use case scripts.
"""

from typing import Dict, Any, List, Optional
from pathlib import Path

from .constants import AMINO_ACIDS, AA_GROUPS


def validate_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate and normalize configuration parameters.

    Args:
        config: Configuration dictionary

    Returns:
        dict: Validated and normalized config
    """
    validated = config.copy()

    # Validate sequence length range
    if 'sequence_length_range' in validated:
        length_range = validated['sequence_length_range']
        if not isinstance(length_range, (list, tuple)) or len(length_range) != 2:
            print("Warning: Invalid sequence_length_range format, using default [6, 15]")
            validated['sequence_length_range'] = [6, 15]
        elif length_range[0] > length_range[1] or length_range[0] < 1:
            print("Warning: Invalid sequence length range values, using default [6, 15]")
            validated['sequence_length_range'] = [6, 15]

    # Validate probability values
    for key in ['cysteine_probability', 'hydrophobic_bias']:
        if key in validated:
            value = validated[key]
            if not isinstance(value, (int, float)) or value < 0 or value > 1:
                print(f"Warning: Invalid {key}, must be between 0 and 1")
                validated[key] = 0.5

    # Validate file paths
    for key in ['input_file', 'model_path']:
        if key in validated and validated[key]:
            path = Path(validated[key])
            if not path.exists():
                print(f"Warning: File not found: {path}")

    return validated


def is_valid_sequence(sequence: str) -> bool:
    """
    Check if sequence contains only valid amino acids.

    Args:
        sequence: Peptide sequence

    Returns:
        bool: True if sequence is valid
    """
    sequence = sequence.upper().strip()
    return len(sequence) > 0 and all(aa in AMINO_ACIDS for aa in sequence)


def validate_cyclic_peptide(sequence: str, min_length: int = 3, max_length: int = 50) -> bool:
    """
    Validate that sequence could form a cyclic peptide.

    Args:
        sequence: Peptide sequence
        min_length: Minimum sequence length
        max_length: Maximum sequence length

    Returns:
        bool: True if sequence is suitable for cyclization
    """
    if not is_valid_sequence(sequence):
        return False

    length = len(sequence)

    # Check length constraints
    if length < min_length or length > max_length:
        return False

    # Check for problematic sequences
    # Too many prolines (rigid)
    if sequence.count('P') > length * 0.3:
        return False

    # Check for minimum complexity
    unique_aas = set(sequence)
    if len(unique_aas) < min(3, length // 2):
        return False

    return True


def check_sequence_quality(sequence: str) -> Dict[str, Any]:
    """
    Assess the quality of a peptide sequence.

    Args:
        sequence: Peptide sequence

    Returns:
        dict: Quality assessment results
    """
    sequence = sequence.upper()
    length = len(sequence)

    if length == 0:
        return {'valid': False, 'error': 'Empty sequence'}

    if not is_valid_sequence(sequence):
        return {'valid': False, 'error': 'Invalid amino acids'}

    # Count properties
    counts = {group: sum(1 for aa in sequence if aa in aas)
              for group, aas in AA_GROUPS.items()}

    # Calculate ratios
    hydrophobic_ratio = counts['hydrophobic'] / length
    polar_ratio = counts['polar'] / length
    charged_ratio = (counts['positive'] + counts['negative']) / length

    # Quality checks
    quality_issues = []

    if hydrophobic_ratio > 0.8:
        quality_issues.append('Too hydrophobic - may aggregate')
    elif hydrophobic_ratio < 0.1:
        quality_issues.append('Too hydrophilic - may be unstable')

    if charged_ratio > 0.5:
        quality_issues.append('Too many charged residues')

    if sequence.count('P') > length * 0.3:
        quality_issues.append('Too many prolines - may be too rigid')

    if sequence.count('C') % 2 == 1:
        quality_issues.append('Odd number of cysteines - unpaired disulfide')

    # Overall assessment
    if len(quality_issues) == 0:
        quality = 'good'
    elif len(quality_issues) <= 2:
        quality = 'acceptable'
    else:
        quality = 'poor'

    return {
        'valid': True,
        'quality': quality,
        'issues': quality_issues,
        'hydrophobic_ratio': hydrophobic_ratio,
        'polar_ratio': polar_ratio,
        'charged_ratio': charged_ratio,
        'length': length,
        'unique_residues': len(set(sequence))
    }


def validate_input_sequences(
    sequences: Dict[str, str],
    strict: bool = False
) -> Dict[str, Dict[str, Any]]:
    """
    Validate a collection of sequences.

    Args:
        sequences: Dict of sequence_id -> sequence
        strict: If True, require high quality sequences

    Returns:
        dict: Validation results for each sequence
    """
    results = {}

    for seq_id, sequence in sequences.items():
        quality = check_sequence_quality(sequence)

        if strict and quality.get('quality') == 'poor':
            quality['reject'] = True
            quality['reason'] = f"Poor quality: {', '.join(quality['issues'])}"
        else:
            quality['reject'] = False

        results[seq_id] = quality

    return results


def filter_valid_sequences(
    sequences: Dict[str, str],
    min_length: int = 3,
    max_length: int = 50,
    require_cyclizable: bool = True
) -> Dict[str, str]:
    """
    Filter sequences to keep only valid ones.

    Args:
        sequences: Dict of sequence_id -> sequence
        min_length: Minimum sequence length
        max_length: Maximum sequence length
        require_cyclizable: If True, check cyclization potential

    Returns:
        dict: Filtered sequences
    """
    filtered = {}

    for seq_id, sequence in sequences.items():
        if is_valid_sequence(sequence):
            if require_cyclizable:
                if validate_cyclic_peptide(sequence, min_length, max_length):
                    filtered[seq_id] = sequence
            else:
                length = len(sequence)
                if min_length <= length <= max_length:
                    filtered[seq_id] = sequence

    return filtered