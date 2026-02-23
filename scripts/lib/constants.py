"""
Constants for cyclic peptide analysis.

Extracted from repo/PepFlowww/data/residue_constants.py and use case scripts.
These are the core amino acid definitions and properties needed for peptide analysis.
"""

# Standard 20 amino acids (alphabetically sorted as in original repo)
AMINO_ACIDS = [
    "A", "R", "N", "D", "C", "Q", "E", "G", "H", "I",
    "L", "K", "M", "F", "P", "S", "T", "W", "Y", "V"
]

# Mapping from amino acid to index
AMINO_ACID_ORDER = {aa: i for i, aa in enumerate(AMINO_ACIDS)}

# Amino acid property groups for analysis
AA_GROUPS = {
    'hydrophobic': ['A', 'V', 'I', 'L', 'M', 'F', 'W', 'Y'],
    'polar': ['S', 'T', 'N', 'Q'],
    'positive': ['K', 'R', 'H'],
    'negative': ['D', 'E'],
    'special': ['C', 'P', 'G']
}

# Comprehensive amino acid properties
AA_PROPERTIES = {
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
    },
    'charge_ph7': {  # Charge at physiological pH
        'R': 1, 'K': 1, 'H': 0.5, 'D': -1, 'E': -1,
        # All others are 0
        **{aa: 0 for aa in AMINO_ACIDS if aa not in ['R', 'K', 'H', 'D', 'E']}
    }
}

# Natural amino acid frequencies (approximate, from protein databases)
NATURAL_FREQUENCIES = {
    'A': 0.074, 'R': 0.042, 'N': 0.044, 'D': 0.059, 'C': 0.033,
    'Q': 0.037, 'E': 0.058, 'G': 0.074, 'H': 0.029, 'I': 0.053,
    'L': 0.093, 'K': 0.059, 'M': 0.025, 'F': 0.045, 'P': 0.039,
    'S': 0.067, 'T': 0.068, 'W': 0.013, 'Y': 0.033, 'V': 0.068
}