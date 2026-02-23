"""
I/O utilities for peptide sequence files.

Simplified from repo code to handle FASTA, CSV, and other common formats
without complex dependencies.
"""

from pathlib import Path
from typing import Dict, List, Union, Optional
import pandas as pd

from .constants import AMINO_ACIDS


def validate_sequence(sequence: str) -> bool:
    """
    Validate that sequence contains only valid amino acids.

    Args:
        sequence: Peptide sequence string

    Returns:
        bool: True if sequence is valid
    """
    sequence = sequence.upper().strip()
    return all(aa in AMINO_ACIDS for aa in sequence if aa.isalpha())


def parse_fasta(fasta_path: Union[str, Path]) -> Dict[str, str]:
    """
    Parse FASTA file to extract sequences.

    Simplified from use case scripts.

    Args:
        fasta_path: Path to FASTA file

    Returns:
        dict: Mapping of sequence_id -> sequence
    """
    sequences = {}
    current_id = None
    current_seq = ""

    fasta_path = Path(fasta_path)

    if not fasta_path.exists():
        raise FileNotFoundError(f"FASTA file not found: {fasta_path}")

    with open(fasta_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line.startswith('>'):
                # Save previous sequence
                if current_id is not None:
                    sequences[current_id] = current_seq.upper()
                # Start new sequence
                current_id = line[1:]  # Remove '>'
                current_seq = ""
            else:
                current_seq += line

        # Add last sequence
        if current_id is not None:
            sequences[current_id] = current_seq.upper()

    return sequences


def save_sequences_fasta(
    sequences: List[Dict[str, str]],
    output_file: Union[str, Path]
) -> None:
    """
    Save sequences to FASTA format.

    Args:
        sequences: List of dicts with 'id' and 'sequence' keys
        output_file: Path to output file
    """
    output_file = Path(output_file)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w') as f:
        for seq_data in sequences:
            seq_id = seq_data.get('id', 'unknown')
            sequence = seq_data.get('sequence', '')
            f.write(f">{seq_id}\n{sequence}\n")


def save_sequences_csv(
    sequences: List[Dict[str, str]],
    output_file: Union[str, Path]
) -> None:
    """
    Save sequences to CSV format with metadata.

    Args:
        sequences: List of dicts with sequence data and metadata
        output_file: Path to output file
    """
    output_file = Path(output_file)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    df = pd.DataFrame(sequences)
    df.to_csv(output_file, index=False)


def load_sequences(input_file: Union[str, Path]) -> Dict[str, str]:
    """
    Load sequences from file (auto-detect format).

    Args:
        input_file: Path to input file

    Returns:
        dict: Mapping of sequence_id -> sequence
    """
    input_file = Path(input_file)

    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")

    # Auto-detect format
    if input_file.suffix.lower() in ['.fasta', '.fa', '.fas']:
        return parse_fasta(input_file)
    elif input_file.suffix.lower() == '.csv':
        df = pd.read_csv(input_file)
        if 'sequence' in df.columns:
            id_col = 'id' if 'id' in df.columns else 'sequence_id'
            if id_col not in df.columns:
                # Generate IDs
                ids = [f"seq_{i:03d}" for i in range(len(df))]
            else:
                ids = df[id_col]
            return dict(zip(ids, df['sequence']))
        else:
            raise ValueError("CSV file must contain 'sequence' column")
    else:
        # Try as FASTA
        try:
            return parse_fasta(input_file)
        except:
            raise ValueError(f"Unsupported file format: {input_file.suffix}")


def save_dataframe_results(
    results: Dict[str, pd.DataFrame],
    output_prefix: Union[str, Path]
) -> List[str]:
    """
    Save multiple dataframes with a common prefix.

    Args:
        results: Dict of name -> dataframe
        output_prefix: Base path for outputs

    Returns:
        list: Paths to created files
    """
    output_prefix = Path(output_prefix)
    output_prefix.parent.mkdir(parents=True, exist_ok=True)

    created_files = []

    for name, df in results.items():
        if isinstance(df, pd.DataFrame):
            file_path = output_prefix.parent / f"{output_prefix.stem}_{name}.csv"
            df.to_csv(file_path, index=False)
            created_files.append(str(file_path))

    return created_files