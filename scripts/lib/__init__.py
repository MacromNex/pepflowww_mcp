"""
Shared library for cyclic peptide MCP scripts.

These are extracted and simplified functions from the PepFlowww repository
to minimize dependencies and provide common functionality across scripts.
"""

from .constants import AMINO_ACIDS, AMINO_ACID_ORDER, AA_PROPERTIES, AA_GROUPS
from .io import parse_fasta, save_sequences_fasta, save_sequences_csv, validate_sequence
from .validation import validate_config, validate_cyclic_peptide, is_valid_sequence
from .utils import calculate_basic_properties, balance_charges

__all__ = [
    'AMINO_ACIDS', 'AMINO_ACID_ORDER', 'AA_PROPERTIES', 'AA_GROUPS',
    'parse_fasta', 'save_sequences_fasta', 'save_sequences_csv', 'validate_sequence',
    'validate_config', 'validate_cyclic_peptide', 'is_valid_sequence',
    'calculate_basic_properties', 'balance_charges'
]