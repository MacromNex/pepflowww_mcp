#!/usr/bin/env python3
"""
Run All PepFlowww Examples

This script runs all the use case examples in sequence to demonstrate
the complete PepFlowww workflow for cyclic peptide design.

Usage:
    python examples/run_all_examples.py [--quick]
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path

def run_command(cmd, description, check_success=True):
    """Run a command and handle errors"""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {cmd}")
    print(f"{'='*60}")

    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

        if result.stdout:
            print("STDOUT:")
            print(result.stdout)

        if result.stderr and result.returncode != 0:
            print("STDERR:")
            print(result.stderr)

        if check_success and result.returncode != 0:
            print(f"❌ Command failed with return code: {result.returncode}")
            return False
        else:
            print(f"✅ Command completed")
            return True

    except Exception as e:
        print(f"❌ Error running command: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Run all PepFlowww examples")
    parser.add_argument('--quick', action='store_true',
                       help='Run quick versions of examples (fewer iterations/samples)')
    parser.add_argument('--skip_training', action='store_true',
                       help='Skip training example (takes longest)')

    args = parser.parse_args()

    print("🧬 PepFlowww Complete Workflow Demo")
    print("=" * 60)
    print("This script demonstrates the full cyclic peptide design pipeline:")
    print("1. Structure parsing and preprocessing")
    print("2. Peptide sequence analysis")
    print("3. Model training (demo)")
    print("4. Peptide sampling/generation")
    print("5. Structure inference/prediction")
    print()

    # Set parameters based on quick mode
    if args.quick:
        print("🚀 Running in QUICK mode (reduced iterations/samples)")
        train_iters = 10
        samples = 3
        steps = 10
    else:
        print("🐌 Running in FULL mode (normal iterations/samples)")
        train_iters = 100
        samples = 8
        steps = 50

    results = []
    base_dir = Path(__file__).parent

    # Example 1: Structure parsing
    print(f"\n📋 Step 1: Structure Parsing and Preprocessing")
    cmd = f"cd {base_dir} && python use_case_4_structure_parsing.py --create_demo --output structure_analysis/"
    success = run_command(cmd, "Structure parsing with demo data")
    results.append(("Structure Parsing", success))

    # Example 2: Sequence analysis
    print(f"\n🧪 Step 2: Peptide Sequence Analysis")
    cmd = f"cd {base_dir} && python use_case_5_peptide_analysis.py --create_demo --output peptide_analysis/"
    success = run_command(cmd, "Peptide sequence analysis")
    results.append(("Sequence Analysis", success))

    # Example 3: Training (optional)
    if not args.skip_training:
        print(f"\n🏋️ Step 3: Model Training (Demo)")
        cmd = f"cd {base_dir} && python use_case_1_train_model.py --config data/config_demo.yaml --device cpu --max_iters {train_iters}"
        success = run_command(cmd, f"Model training demo ({train_iters} iterations)", check_success=False)
        results.append(("Model Training", success))
    else:
        print(f"\n⏭️ Step 3: Skipping Model Training")
        results.append(("Model Training", "Skipped"))

    # Example 4: Peptide sampling
    print(f"\n🎲 Step 4: Peptide Sampling/Generation")
    cmd = f"cd {base_dir} && python use_case_2_sample_peptides.py --output generated_peptides/ --num_samples {samples} --num_steps {steps} --device cpu"
    success = run_command(cmd, f"Peptide sampling ({samples} samples, {steps} steps)", check_success=False)
    results.append(("Peptide Sampling", success))

    # Example 5: Structure inference
    print(f"\n🔮 Step 5: Structure Inference/Prediction")
    cmd = f"cd {base_dir} && python use_case_3_structure_inference.py --sequence CYCLIGKRC --output predicted_peptide.pdb --num_steps {steps} --device cpu"
    success = run_command(cmd, f"Structure inference ({steps} steps)", check_success=False)
    results.append(("Structure Inference", success))

    # Summary
    print(f"\n🎯 WORKFLOW SUMMARY")
    print("=" * 60)

    for step, result in results:
        if result == "Skipped":
            status = "⏭️ Skipped"
        elif result:
            status = "✅ Success"
        else:
            status = "⚠️ Completed with warnings"
        print(f"{step:20} : {status}")

    print(f"\n📁 Output files created:")
    output_dirs = [
        "structure_analysis/",
        "peptide_analysis/",
        "generated_peptides/",
        "predicted_peptide.pdb"
    ]

    for output in output_dirs:
        output_path = base_dir / output
        if output_path.exists():
            print(f"  ✅ {output}")
        else:
            print(f"  ❌ {output} (not found)")

    print(f"\n💡 Next Steps:")
    print("1. Examine the generated files in each output directory")
    print("2. Use real training data for actual model development")
    print("3. Validate generated peptides using molecular dynamics")
    print("4. Integrate with experimental validation workflows")

    total_success = sum(1 for _, result in results if result is True)
    total_attempts = len([r for r in results if r[1] != "Skipped"])

    print(f"\n🎉 Workflow completed: {total_success}/{total_attempts} steps successful")

if __name__ == '__main__':
    main()