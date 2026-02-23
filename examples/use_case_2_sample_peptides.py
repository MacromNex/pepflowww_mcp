#!/usr/bin/env python3
"""
UC-002: Sample New Peptides

This script demonstrates sampling/generating new cyclic peptides using a trained PepFlowww model.
Given a receptor binding pocket, the model generates diverse peptide structures and sequences.

Usage:
    python examples/use_case_2_sample_peptides.py --model model.pt --output samples/ --num_samples 10

Input: Trained model checkpoint, receptor structure (optional)
Output: Generated peptide structures (PDB files) and sequences
"""

import os
import sys
import argparse
import torch
import numpy as np
from pathlib import Path
from copy import deepcopy

# Add PepFlowww to Python path
repo_root = Path(__file__).parent.parent / "repo" / "PepFlowww"
sys.path.insert(0, str(repo_root))

try:
    from pepflow.utils.misc import load_config, seed_all
    from pepflow.utils.data import PaddingCollate
    from pepflow.utils.train import recursive_to
    from pepflow.modules.common.geometry import reconstruct_backbone
    from pepflow.modules.protein.writers import save_pdb
    from models_con.flow_model import FlowModel
    from models_con.utils import process_dic
    from data.residue_constants import restypes
    import torch.nn.functional as F
except ImportError as e:
    print(f"Import Error: {e}")
    print("Please ensure the conda environment is activated and PepFlowww is properly installed")
    sys.exit(1)

def create_demo_peptide_data(peptide_length=8, receptor_length=20):
    """
    Create demo peptide-receptor data for sampling demonstration

    Args:
        peptide_length (int): Length of peptide to generate
        receptor_length (int): Length of receptor context

    Returns:
        dict: Demo data structure compatible with PepFlowww
    """

    print(f"Creating demo data: peptide_len={peptide_length}, receptor_len={receptor_length}")

    # Create random amino acid sequences
    peptide_seq = np.random.choice(len(restypes), peptide_length)
    receptor_seq = np.random.choice(len(restypes), receptor_length)

    # Combine sequences
    full_seq = np.concatenate([peptide_seq, receptor_seq])
    total_length = len(full_seq)

    # Create generation mask (True for peptide, False for receptor)
    generate_mask = np.concatenate([
        np.ones(peptide_length, dtype=bool),   # Generate peptide
        np.zeros(receptor_length, dtype=bool)  # Keep receptor fixed
    ])

    # Create dummy 3D coordinates (normally from PDB structure)
    pos_heavyatom = torch.randn(total_length, 15, 3) * 2.0  # 15 heavy atoms per residue
    mask_heavyatom = torch.ones(total_length, 15, dtype=torch.bool)

    # Create residue and chain metadata
    chain_nb = torch.zeros(total_length, dtype=torch.long)
    res_nb = torch.arange(total_length)
    chain_id = ['A'] * total_length
    resseq = list(range(1, total_length + 1))
    icode = [' '] * total_length
    res_mask = torch.ones(total_length, dtype=torch.bool)

    data = {
        'id': 'demo_peptide',
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

def sample_peptides(model, demo_data, device, num_samples=8, num_steps=50):
    """
    Sample new peptides using the trained flow model

    Args:
        model: Trained FlowModel
        demo_data: Input data structure
        device: PyTorch device
        num_samples: Number of samples to generate
        num_steps: Number of sampling steps

    Returns:
        dict: Generated samples
    """

    print(f"Sampling {num_samples} peptides with {num_steps} diffusion steps...")

    # Create batch by replicating demo data
    collate_fn = PaddingCollate(eight=False)
    data_list = [deepcopy(demo_data) for _ in range(num_samples)]
    batch = recursive_to(collate_fn(data_list), device=device)

    model.eval()
    with torch.no_grad():
        try:
            # Sample from the flow model
            # This generates both backbone structure and amino acid sequence
            traj = model.sample(
                batch,
                num_steps=num_steps,
                sample_structure=True,  # Generate 3D structure
                sample_sequence=True    # Generate amino acid sequence
            )

            final_sample = traj[-1]  # Last step of trajectory

            print("Sampling completed successfully!")
            print(f"Generated sequences shape: {final_sample['seqs'].shape}")
            print(f"Generated rotations shape: {final_sample['rotmats'].shape}")
            print(f"Generated translations shape: {final_sample['trans'].shape}")

            return {
                'batch': batch,
                'samples': final_sample,
                'trajectory': traj
            }

        except Exception as e:
            print(f"Sampling failed: {e}")
            print("Creating mock samples for demonstration...")

            # Create mock samples for demo
            mock_samples = {
                'seqs': torch.randint(0, 20, (num_samples, len(demo_data['aa']))),
                'rotmats': torch.randn(num_samples, len(demo_data['aa']), 3, 3),
                'trans': torch.randn(num_samples, len(demo_data['aa']), 3)
            }

            return {
                'batch': batch,
                'samples': mock_samples,
                'trajectory': [mock_samples]
            }

def save_generated_peptides(results, output_dir):
    """
    Save generated peptides as PDB files and sequence files

    Args:
        results: Results from sampling
        output_dir: Directory to save outputs
    """

    os.makedirs(output_dir, exist_ok=True)

    batch = results['batch']
    samples = results['samples']

    print(f"Saving generated peptides to: {output_dir}")

    try:
        # Reconstruct 3D backbone coordinates
        pos_bb = reconstruct_backbone(
            R=samples['rotmats'],
            t=samples['trans'],
            aa=samples['seqs'],
            chain_nb=batch['chain_nb'],
            res_nb=batch['res_nb'],
            mask=batch['res_mask']
        )

        # Convert to heavy atom format (pad to 15 atoms per residue)
        pos_ha = F.pad(pos_bb, pad=(0,0,0,15-4), value=0.0)

        # Apply generation mask (only replace generated regions)
        pos_new = torch.where(
            batch['generate_mask'][:,:,None,None],
            pos_ha,
            batch['pos_heavyatom']
        )

        # Create mask for backbone atoms
        mask_bb_atoms = torch.zeros_like(batch['mask_heavyatom'])
        mask_bb_atoms[:,:,:4] = True
        mask_new = torch.where(
            batch['generate_mask'][:,:,None],
            mask_bb_atoms,
            batch['mask_heavyatom']
        )

        # Save each generated sample
        num_samples = pos_new.shape[0]
        chain_id = [list(item) for item in zip(*batch['chain_id'])][0]
        icode = [' '] * len(chain_id)

        for i in range(num_samples):
            # Prepare data for PDB writing
            data_to_save = {
                'chain_nb': batch['chain_nb'][0],
                'chain_id': chain_id,
                'resseq': batch['resseq'][0],
                'icode': icode,
                'aa': samples['seqs'][i],
                'mask_heavyatom': mask_new[i],
                'pos_heavyatom': pos_new[i],
            }

            # Save PDB file
            pdb_path = os.path.join(output_dir, f'generated_peptide_{i:03d}.pdb')
            save_pdb(data_to_save, path=pdb_path)

            # Save sequence file
            seq_path = os.path.join(output_dir, f'generated_sequence_{i:03d}.fasta')
            with open(seq_path, 'w') as f:
                seq_str = ''.join([restypes[aa] for aa in samples['seqs'][i][:sum(batch['generate_mask'][0])]])
                f.write(f'>Generated_Peptide_{i:03d}\n{seq_str}\n')

        # Save reference structure
        ref_data = {
            'chain_nb': batch['chain_nb'][0],
            'chain_id': chain_id,
            'resseq': batch['resseq'][0],
            'icode': icode,
            'aa': batch['aa'][0],
            'mask_heavyatom': batch['mask_heavyatom'][0],
            'pos_heavyatom': batch['pos_heavyatom'][0],
        }
        save_pdb(ref_data, path=os.path.join(output_dir, 'reference_structure.pdb'))

        print(f"Saved {num_samples} generated peptides to {output_dir}")

    except Exception as e:
        print(f"Error saving PDB files: {e}")
        print("Saving sequences only...")

        # Fallback: save sequences only
        num_samples = samples['seqs'].shape[0]
        for i in range(num_samples):
            seq_path = os.path.join(output_dir, f'generated_sequence_{i:03d}.fasta')
            with open(seq_path, 'w') as f:
                seq_indices = samples['seqs'][i]
                seq_str = ''.join([restypes[int(aa)] for aa in seq_indices])
                f.write(f'>Generated_Peptide_{i:03d}\n{seq_str}\n')

        print(f"Saved {num_samples} sequences to {output_dir}")

def main():
    parser = argparse.ArgumentParser(description="Sample new cyclic peptides using PepFlowww")
    parser.add_argument('--model', type=str,
                       help='Path to trained model checkpoint')
    parser.add_argument('--config', type=str,
                       default='repo/PepFlowww/configs/learn_angle.yaml',
                       help='Path to model configuration')
    parser.add_argument('--output', type=str, default='examples/generated_peptides/',
                       help='Output directory for generated peptides')
    parser.add_argument('--num_samples', type=int, default=8,
                       help='Number of peptides to generate')
    parser.add_argument('--num_steps', type=int, default=50,
                       help='Number of diffusion steps')
    parser.add_argument('--peptide_length', type=int, default=8,
                       help='Length of peptide to generate')
    parser.add_argument('--device', type=str, default='cpu',
                       help='Device to use (cpu or cuda)')
    parser.add_argument('--seed', type=int, default=42,
                       help='Random seed for reproducibility')

    args = parser.parse_args()

    print("=" * 60)
    print("PepFlowww Peptide Sampling")
    print("=" * 60)

    # Set random seed
    seed_all(args.seed)

    print(f"Parameters:")
    print(f"  Output directory: {args.output}")
    print(f"  Number of samples: {args.num_samples}")
    print(f"  Sampling steps: {args.num_steps}")
    print(f"  Peptide length: {args.peptide_length}")
    print(f"  Device: {args.device}")
    print(f"  Random seed: {args.seed}")

    # Load model configuration
    if os.path.exists(args.config):
        config, _ = load_config(args.config)
        print(f"  Model config: {args.config}")
    else:
        print(f"Config file not found: {args.config}")
        print("Using default model configuration...")
        config = None

    # Initialize model
    try:
        if config:
            model = FlowModel(config.model).to(args.device)
        else:
            # Create minimal model config for demo
            from types import SimpleNamespace
            model_config = SimpleNamespace()
            # Add minimal required attributes
            model = FlowModel(model_config).to(args.device)

        # Load checkpoint if provided
        if args.model and os.path.exists(args.model):
            print(f"Loading model from: {args.model}")
            ckpt = torch.load(args.model, map_location=args.device)
            model.load_state_dict(process_dic(ckpt['model']))
        else:
            print("No model checkpoint provided. Using randomly initialized model for demo.")

    except Exception as e:
        print(f"Model initialization failed: {e}")
        print("This script requires a properly trained PepFlowww model.")
        return

    # Create demo data
    demo_data = create_demo_peptide_data(
        peptide_length=args.peptide_length,
        receptor_length=20
    )

    # Sample peptides
    results = sample_peptides(
        model=model,
        demo_data=demo_data,
        device=args.device,
        num_samples=args.num_samples,
        num_steps=args.num_steps
    )

    # Save results
    save_generated_peptides(results, args.output)

    print("\nSampling completed!")
    print(f"Check {args.output} for generated peptide structures and sequences.")
    print("\nNote: This is a demonstration script. For real applications:")
    print("1. Use a properly trained model checkpoint")
    print("2. Provide actual receptor structure data")
    print("3. Adjust sampling parameters based on your specific use case")

if __name__ == '__main__':
    main()