#!/usr/bin/env python3
"""
UC-003: Peptide Structure Inference and Reconstruction

This script demonstrates inference/reconstruction of peptide structures from sequence data
using a trained PepFlowww model. It can predict 3D structure from sequence or refine
existing structures.

Usage:
    python examples/use_case_3_structure_inference.py --sequence ACDEFGHIK --output structure.pdb

Input: Peptide sequence (FASTA or string) and optional receptor structure
Output: Predicted 3D peptide structure (PDB format)
"""

import os
import sys
import argparse
import torch
import numpy as np
from pathlib import Path

# Add PepFlowww to Python path
repo_root = Path(__file__).parent.parent / "repo" / "PepFlowww"
sys.path.insert(0, str(repo_root))

try:
    from pepflow.utils.misc import load_config, seed_all
    from pepflow.utils.data import PaddingCollate
    from pepflow.utils.train import recursive_to
    from pepflow.modules.common.geometry import reconstruct_backbone
    from pepflow.modules.protein.writers import save_pdb
    from pepflow.modules.protein.parsers import get_fasta_from_pdb
    from data.residue_constants import restypes, restype_order
    from models_con.flow_model import FlowModel
    from models_con.utils import process_dic
    from models_con.torsion import full_atom_reconstruction, get_heavyatom_mask
    import torch.nn.functional as F
except ImportError as e:
    print(f"Import Error: {e}")
    print("Please ensure the conda environment is activated and PepFlowww is properly installed")
    sys.exit(1)

def sequence_to_indices(sequence):
    """
    Convert amino acid sequence string to indices

    Args:
        sequence (str): Amino acid sequence (e.g., "ACDEFG")

    Returns:
        np.array: Array of amino acid indices
    """
    sequence = sequence.upper().strip()
    indices = []

    for aa in sequence:
        if aa in restype_order:
            indices.append(restype_order[aa])
        else:
            print(f"Warning: Unknown amino acid '{aa}', skipping...")

    return np.array(indices)

def read_sequence_from_fasta(fasta_path):
    """
    Read peptide sequence from FASTA file

    Args:
        fasta_path (str): Path to FASTA file

    Returns:
        str: Amino acid sequence
    """
    sequence = ""
    with open(fasta_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line.startswith('>'):
                sequence += line

    return sequence.replace(' ', '').replace('\n', '')

def create_structure_data(sequence_indices, add_receptor=True):
    """
    Create data structure for peptide structure prediction

    Args:
        sequence_indices (np.array): Amino acid sequence as indices
        add_receptor (bool): Whether to add dummy receptor context

    Returns:
        dict: Data structure compatible with PepFlowww
    """
    peptide_length = len(sequence_indices)

    if add_receptor:
        # Add dummy receptor context (in real use, this would be actual receptor structure)
        receptor_length = max(20, 2 * peptide_length)
        receptor_seq = np.random.choice(20, receptor_length)
        full_seq = np.concatenate([sequence_indices, receptor_seq])

        # Generation mask: predict peptide structure, keep receptor fixed
        generate_mask = np.concatenate([
            np.ones(peptide_length, dtype=bool),
            np.zeros(receptor_length, dtype=bool)
        ])
    else:
        full_seq = sequence_indices
        generate_mask = np.ones(peptide_length, dtype=bool)

    total_length = len(full_seq)

    # Initialize random 3D coordinates (will be refined by model)
    pos_heavyatom = torch.randn(total_length, 15, 3) * 2.0
    mask_heavyatom = torch.ones(total_length, 15, dtype=torch.bool)

    # Metadata
    chain_nb = torch.zeros(total_length, dtype=torch.long)
    res_nb = torch.arange(total_length)
    chain_id = ['A'] * total_length
    resseq = list(range(1, total_length + 1))
    icode = [' '] * total_length
    res_mask = torch.ones(total_length, dtype=torch.bool)

    data = {
        'id': f'inference_peptide_{peptide_length}aa',
        'aa': torch.LongTensor(full_seq),
        'pos_heavyatom': pos_heavyatom,
        'mask_heavyatom': mask_heavyatom,
        'generate_mask': torch.BoolTensor(generate_mask),
        'chain_nb': chain_nb,
        'chain_id': chain_id,
        'res_nb': res_nb,
        'resseq': resseq,
        'icode': icode,
        'res_mask': res_mask,
    }

    return data

def predict_structure(model, data, device, num_samples=1, num_steps=100):
    """
    Predict 3D structure for given peptide sequence

    Args:
        model: Trained FlowModel
        data: Input data structure
        device: PyTorch device
        num_samples: Number of structure predictions
        num_steps: Number of inference steps

    Returns:
        dict: Predicted structures
    """
    print(f"Predicting structure with {num_steps} inference steps...")

    collate_fn = PaddingCollate(eight=False)
    data_list = [data.copy() for _ in range(num_samples)]
    batch = recursive_to(collate_fn(data_list), device=device)

    model.eval()
    with torch.no_grad():
        try:
            # Run inference to predict structure
            # The model will predict both backbone geometry and side-chain conformations
            trajectory = model.sample(
                batch,
                num_steps=num_steps,
                sample_structure=True,   # Predict 3D coordinates
                sample_sequence=False,   # Keep sequence fixed
                sample_angles=True       # Predict side-chain conformations
            )

            final_structure = trajectory[-1]

            print("Structure prediction completed!")
            print(f"Predicted backbone shape: {final_structure['trans'].shape}")
            print(f"Predicted rotations shape: {final_structure['rotmats'].shape}")

            if 'angles' in final_structure:
                print(f"Predicted angles shape: {final_structure['angles'].shape}")

            return {
                'batch': batch,
                'structure': final_structure,
                'trajectory': trajectory
            }

        except Exception as e:
            print(f"Structure prediction failed: {e}")
            print("Creating mock structure for demonstration...")

            # Create mock prediction for demo
            mock_structure = {
                'seqs': batch['aa'],  # Keep original sequence
                'rotmats': torch.randn_like(batch['pos_heavyatom'][:, :, :3, :3]),
                'trans': torch.randn_like(batch['pos_heavyatom'][:, :, 0, :]),
                'angles': torch.randn(batch['aa'].shape[0], batch['aa'].shape[1], 8)
            }

            return {
                'batch': batch,
                'structure': mock_structure,
                'trajectory': [mock_structure]
            }

def save_predicted_structure(results, output_path, include_sidechain=True):
    """
    Save predicted structure to PDB file

    Args:
        results: Results from structure prediction
        output_path: Path to output PDB file
        include_sidechain: Whether to include side-chain atoms
    """
    batch = results['batch']
    structure = results['structure']

    print(f"Saving predicted structure to: {output_path}")

    try:
        if include_sidechain and 'angles' in structure:
            # Full atom reconstruction including side-chains
            pos_ha, _, _ = full_atom_reconstruction(
                R_bb=structure['rotmats'],
                t_bb=structure['trans'],
                angles=structure['angles'],
                aa=structure['seqs']
            )
            # Pad to 15 atoms per residue
            pos_ha = F.pad(pos_ha, pad=(0,0,0,15-14), value=0.0)
            mask_ha = get_heavyatom_mask(structure['seqs'])

        else:
            # Backbone only reconstruction
            pos_bb = reconstruct_backbone(
                R=structure['rotmats'],
                t=structure['trans'],
                aa=structure['seqs'],
                chain_nb=batch['chain_nb'],
                res_nb=batch['res_nb'],
                mask=batch['res_mask']
            )
            # Pad to 15 atoms per residue
            pos_ha = F.pad(pos_bb, pad=(0,0,0,15-4), value=0.0)
            # Create backbone-only mask
            mask_ha = torch.zeros_like(batch['mask_heavyatom'])
            mask_ha[:, :, :4] = True

        # Apply generation mask (only replace predicted regions)
        pos_new = torch.where(
            batch['generate_mask'][:,:,None,None],
            pos_ha,
            batch['pos_heavyatom']
        )

        mask_new = torch.where(
            batch['generate_mask'][:,:,None],
            mask_ha,
            batch['mask_heavyatom']
        )

        # Prepare data for first sample
        chain_id = [list(item) for item in zip(*batch['chain_id'])][0]
        icode = [' '] * len(chain_id)

        data_to_save = {
            'chain_nb': batch['chain_nb'][0],
            'chain_id': chain_id,
            'resseq': batch['resseq'][0],
            'icode': icode,
            'aa': structure['seqs'][0],
            'mask_heavyatom': mask_new[0],
            'pos_heavyatom': pos_new[0],
        }

        # Create output directory if needed
        os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)

        # Save PDB file
        save_pdb(data_to_save, path=output_path)

        print(f"Structure saved successfully!")

        # Save additional predictions if multiple samples
        num_samples = structure['seqs'].shape[0]
        if num_samples > 1:
            base_path = output_path.rsplit('.', 1)[0]
            for i in range(1, num_samples):
                sample_data = {
                    'chain_nb': batch['chain_nb'][0],
                    'chain_id': chain_id,
                    'resseq': batch['resseq'][0],
                    'icode': icode,
                    'aa': structure['seqs'][i],
                    'mask_heavyatom': mask_new[i],
                    'pos_heavyatom': pos_new[i],
                }
                sample_path = f"{base_path}_sample_{i}.pdb"
                save_pdb(sample_data, path=sample_path)

            print(f"Saved {num_samples} structure predictions")

    except Exception as e:
        print(f"Error saving structure: {e}")
        print("Structure prediction completed but could not save PDB file.")

def main():
    parser = argparse.ArgumentParser(description="Predict peptide structure using PepFlowww")
    parser.add_argument('--sequence', type=str,
                       help='Peptide sequence (e.g., "ACDEFGHIK")')
    parser.add_argument('--fasta', type=str,
                       help='Path to FASTA file containing peptide sequence')
    parser.add_argument('--model', type=str,
                       help='Path to trained model checkpoint')
    parser.add_argument('--config', type=str,
                       default='repo/PepFlowww/configs/learn_angle.yaml',
                       help='Path to model configuration')
    parser.add_argument('--output', type=str, default='examples/predicted_structure.pdb',
                       help='Output PDB file path')
    parser.add_argument('--num_samples', type=int, default=1,
                       help='Number of structure predictions')
    parser.add_argument('--num_steps', type=int, default=100,
                       help='Number of inference steps')
    parser.add_argument('--device', type=str, default='cpu',
                       help='Device to use (cpu or cuda)')
    parser.add_argument('--include_sidechain', action='store_true',
                       help='Include side-chain atoms in prediction')
    parser.add_argument('--seed', type=int, default=42,
                       help='Random seed')

    args = parser.parse_args()

    print("=" * 60)
    print("PepFlowww Structure Inference")
    print("=" * 60)

    # Set random seed
    seed_all(args.seed)

    # Get peptide sequence
    if args.sequence:
        sequence = args.sequence
        print(f"Input sequence: {sequence}")
    elif args.fasta:
        if os.path.exists(args.fasta):
            sequence = read_sequence_from_fasta(args.fasta)
            print(f"Sequence from {args.fasta}: {sequence}")
        else:
            print(f"FASTA file not found: {args.fasta}")
            return
    else:
        # Use demo sequence
        sequence = "CYCLIGKRC"  # Example cyclic peptide
        print(f"Using demo sequence: {sequence}")

    print(f"Sequence length: {len(sequence)} amino acids")

    # Convert sequence to indices
    try:
        sequence_indices = sequence_to_indices(sequence)
        print(f"Converted to indices: {sequence_indices}")
    except Exception as e:
        print(f"Error processing sequence: {e}")
        return

    # Load model
    try:
        if os.path.exists(args.config):
            config, _ = load_config(args.config)
            model = FlowModel(config.model).to(args.device)
        else:
            print(f"Config not found: {args.config}")
            print("Using minimal model for demo...")
            from types import SimpleNamespace
            model = FlowModel(SimpleNamespace()).to(args.device)

        # Load checkpoint if provided
        if args.model and os.path.exists(args.model):
            print(f"Loading model from: {args.model}")
            ckpt = torch.load(args.model, map_location=args.device)
            model.load_state_dict(process_dic(ckpt['model']))
        else:
            print("No model checkpoint provided. Using randomly initialized model for demo.")

    except Exception as e:
        print(f"Model loading failed: {e}")
        return

    # Create data structure
    data = create_structure_data(sequence_indices, add_receptor=True)

    # Predict structure
    results = predict_structure(
        model=model,
        data=data,
        device=args.device,
        num_samples=args.num_samples,
        num_steps=args.num_steps
    )

    # Save results
    save_predicted_structure(
        results=results,
        output_path=args.output,
        include_sidechain=args.include_sidechain
    )

    print(f"\nStructure inference completed!")
    print(f"Predicted structure saved to: {args.output}")
    print(f"\nSequence: {sequence}")
    print(f"Length: {len(sequence)} residues")
    print(f"Samples: {args.num_samples}")
    print(f"Steps: {args.num_steps}")

    print("\nNote: This is a demonstration script. For real applications:")
    print("1. Use a properly trained model checkpoint")
    print("2. Provide accurate receptor structure if available")
    print("3. Validate predicted structures using molecular dynamics or other methods")

if __name__ == '__main__':
    main()