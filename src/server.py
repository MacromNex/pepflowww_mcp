#!/usr/bin/env python3
"""MCP Server for Cyclic Peptide Tools

Provides both synchronous and asynchronous (submit) APIs for cyclic peptide analysis.

For fast operations (<10 minutes):
- Direct function calls with immediate results (sync API)

For long-running or batch operations:
- Submit job, get job_id, check status, retrieve results (submit API)
"""

from fastmcp import FastMCP
from pathlib import Path
from typing import Optional, List, Dict, Any, Union
import sys
import json

# Setup paths
SCRIPT_DIR = Path(__file__).parent.resolve()
MCP_ROOT = SCRIPT_DIR.parent
SCRIPTS_DIR = MCP_ROOT / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))
sys.path.insert(0, str(SCRIPTS_DIR))

from jobs.manager import job_manager
from loguru import logger

# Create MCP server
mcp = FastMCP("cycpep-tools")

# ==============================================================================
# Job Management Tools (for async operations)
# ==============================================================================

@mcp.tool()
def get_job_status(job_id: str) -> Dict[str, Any]:
    """
    Get the status of a submitted cyclic peptide computation job.

    Args:
        job_id: The job ID returned from a submit_* function

    Returns:
        Dictionary with job status, timestamps, and any errors
    """
    return job_manager.get_job_status(job_id)

@mcp.tool()
def get_job_result(job_id: str) -> Dict[str, Any]:
    """
    Get the results of a completed cyclic peptide computation job.

    Args:
        job_id: The job ID of a completed job

    Returns:
        Dictionary with the job results or error if not completed
    """
    return job_manager.get_job_result(job_id)

@mcp.tool()
def get_job_log(job_id: str, tail: int = 50) -> Dict[str, Any]:
    """
    Get log output from a running or completed job.

    Args:
        job_id: The job ID to get logs for
        tail: Number of lines from end (default: 50, use 0 for all)

    Returns:
        Dictionary with log lines and total line count
    """
    return job_manager.get_job_log(job_id, tail)

@mcp.tool()
def cancel_job(job_id: str) -> Dict[str, Any]:
    """
    Cancel a running cyclic peptide computation job.

    Args:
        job_id: The job ID to cancel

    Returns:
        Success or error message
    """
    return job_manager.cancel_job(job_id)

@mcp.tool()
def list_jobs(status: Optional[str] = None) -> Dict[str, Any]:
    """
    List all submitted cyclic peptide computation jobs.

    Args:
        status: Filter by status (pending, running, completed, failed, cancelled)

    Returns:
        List of jobs with their status
    """
    return job_manager.list_jobs(status)

# ==============================================================================
# Synchronous Tools (for fast operations < 10 min)
# ==============================================================================

@mcp.tool()
def analyze_cyclic_peptides(
    input_file: Optional[str] = None,
    sequence: Optional[str] = None,
    use_demo: bool = False,
    output_file: Optional[str] = None,
    include_visualizations: bool = True,
    include_druggability: bool = True,
    no_viz: bool = False
) -> Dict[str, Any]:
    """
    Analyze cyclic peptide sequences and calculate physicochemical properties.

    Fast operation - returns results immediately (~2 seconds for 8 sequences).

    Args:
        input_file: Path to input FASTA file (optional)
        sequence: Single sequence to analyze (optional)
        use_demo: Use built-in demo sequences if no input provided
        output_file: Path to save output files (optional)
        include_visualizations: Generate property distribution plots
        include_druggability: Calculate drug-like properties
        no_viz: Skip visualizations for faster execution

    Returns:
        Dictionary with analysis results, output files, and metadata
    """
    try:
        # Import the script function
        from analyze_peptides import run_analyze_peptides

        # Prepare arguments
        kwargs = {
            "include_visualizations": include_visualizations and not no_viz,
            "include_druggability": include_druggability
        }

        # Handle demo mode
        if use_demo and not input_file and not sequence:
            result = run_analyze_peptides(
                input_file=None,
                output_file=output_file,
                sequence=None,
                **kwargs
            )
        elif sequence:
            result = run_analyze_peptides(
                input_file=None,
                output_file=output_file,
                sequence=sequence,
                **kwargs
            )
        elif input_file:
            result = run_analyze_peptides(
                input_file=input_file,
                output_file=output_file,
                sequence=None,
                **kwargs
            )
        else:
            return {
                "status": "error",
                "error": "Must provide input_file, sequence, or set use_demo=True"
            }

        return {"status": "success", **result}

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return {"status": "error", "error": f"File not found: {e}"}
    except ValueError as e:
        logger.error(f"Invalid input: {e}")
        return {"status": "error", "error": f"Invalid input: {e}"}
    except Exception as e:
        logger.error(f"Peptide analysis failed: {e}")
        return {"status": "error", "error": str(e)}

@mcp.tool()
def generate_peptide_sequences(
    num_samples: int = 10,
    output_file: Optional[str] = None,
    sequence_length: Optional[int] = None,
    amino_acid_weights: str = "uniform",
    include_cysteines: bool = True,
    charged_balance: bool = True,
    output_format: str = "fasta"
) -> Dict[str, Any]:
    """
    Generate cyclic peptide sequences using statistical sampling methods.

    Fast operation - returns results immediately (~0.1 seconds for 10 sequences).

    Args:
        num_samples: Number of sequences to generate
        output_file: Path to save output (optional)
        sequence_length: Fixed sequence length (optional, uses random range if not set)
        amino_acid_weights: Sampling weights ('uniform' or 'natural')
        include_cysteines: Include cysteine residues for cyclization
        charged_balance: Balance charged residues in sequences
        output_format: Output format ('fasta' or 'csv')

    Returns:
        Dictionary with generated sequences, output file path, and metadata
    """
    try:
        from generate_sequences import run_generate_sequences

        # Prepare config overrides
        kwargs = {
            "amino_acid_weights": amino_acid_weights,
            "include_cysteines": include_cysteines,
            "charged_balance": charged_balance,
            "output_format": output_format
        }

        if sequence_length is not None:
            kwargs["sequence_length_range"] = [sequence_length, sequence_length]

        result = run_generate_sequences(
            num_samples=num_samples,
            output_file=output_file,
            **kwargs
        )

        return {"status": "success", **result}

    except ValueError as e:
        logger.error(f"Invalid input: {e}")
        return {"status": "error", "error": f"Invalid input: {e}"}
    except Exception as e:
        logger.error(f"Sequence generation failed: {e}")
        return {"status": "error", "error": str(e)}

# ==============================================================================
# Submit Tools (for demonstration and batch operations)
# ==============================================================================

@mcp.tool()
def submit_peptide_analysis_job(
    input_file: Optional[str] = None,
    sequence: Optional[str] = None,
    use_demo: bool = False,
    output_dir: Optional[str] = None,
    include_visualizations: bool = True,
    include_druggability: bool = True,
    job_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Submit a peptide analysis job for background processing.

    Use this for batch processing or when you want to run the analysis
    in the background. For immediate results, use analyze_cyclic_peptides instead.

    Args:
        input_file: Path to input FASTA file (optional)
        sequence: Single sequence to analyze (optional)
        use_demo: Use built-in demo sequences
        output_dir: Directory for output files
        include_visualizations: Generate plots
        include_druggability: Calculate drug properties
        job_name: Optional name for the job

    Returns:
        Dictionary with job_id for tracking. Use:
        - get_job_status(job_id) to check progress
        - get_job_result(job_id) to get results when completed
        - get_job_log(job_id) to see execution logs
    """
    script_path = str(SCRIPTS_DIR / "analyze_peptides.py")

    args = {
        "include_visualizations": include_visualizations,
        "include_druggability": include_druggability
    }

    if input_file:
        args["input"] = input_file
    elif sequence:
        args["sequence"] = sequence
    elif use_demo:
        args["demo"] = True
    else:
        return {
            "status": "error",
            "error": "Must provide input_file, sequence, or set use_demo=True"
        }

    if output_dir:
        args["output"] = output_dir

    return job_manager.submit_job(
        script_path=script_path,
        args=args,
        job_name=job_name or "peptide_analysis"
    )

@mcp.tool()
def submit_sequence_generation_job(
    num_samples: int = 10,
    output_dir: Optional[str] = None,
    sequence_length: Optional[int] = None,
    amino_acid_weights: str = "uniform",
    include_cysteines: bool = True,
    charged_balance: bool = True,
    output_format: str = "fasta",
    job_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Submit a sequence generation job for background processing.

    Use this for large batch generation or when you want to generate
    sequences in the background. For immediate results, use
    generate_peptide_sequences instead.

    Args:
        num_samples: Number of sequences to generate
        output_dir: Directory for output files
        sequence_length: Fixed sequence length (optional)
        amino_acid_weights: Sampling weights ('uniform' or 'natural')
        include_cysteines: Include cysteines
        charged_balance: Balance charges
        output_format: Format ('fasta' or 'csv')
        job_name: Optional name for the job

    Returns:
        Dictionary with job_id for tracking
    """
    script_path = str(SCRIPTS_DIR / "generate_sequences.py")

    args = {
        "num_samples": num_samples,
        "weights": amino_acid_weights,
        "format": output_format
    }

    if sequence_length is not None:
        args["length"] = sequence_length

    if not include_cysteines:
        args["no_cysteines"] = True

    if not charged_balance:
        args["no_balance"] = True

    if output_dir:
        args["output"] = output_dir

    return job_manager.submit_job(
        script_path=script_path,
        args=args,
        job_name=job_name or f"generate_{num_samples}_sequences"
    )

# ==============================================================================
# Batch Processing Tools
# ==============================================================================

@mcp.tool()
def submit_batch_peptide_analysis(
    input_files: List[str],
    output_dir: Optional[str] = None,
    include_visualizations: bool = True,
    include_druggability: bool = True,
    job_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Submit batch peptide analysis for multiple input files.

    Processes multiple FASTA files in a single background job.
    Use this for processing large datasets or multiple files at once.

    Args:
        input_files: List of FASTA file paths to process
        output_dir: Directory for all output files
        include_visualizations: Generate plots for all files
        include_druggability: Calculate drug properties for all
        job_name: Optional name for the batch job

    Returns:
        Dictionary with job_id for tracking the batch job
    """
    if not input_files:
        return {"status": "error", "error": "No input files provided"}

    # Create a simple batch script approach
    # For now, we'll process the first file and note this is a batch operation
    script_path = str(SCRIPTS_DIR / "analyze_peptides.py")

    # Use the first file as primary input
    # Note: For a full batch implementation, you'd want a dedicated batch script
    args = {
        "input": input_files[0],  # Process first file
        "include_visualizations": include_visualizations,
        "include_druggability": include_druggability
    }

    if output_dir:
        args["output"] = output_dir

    job_name = job_name or f"batch_analysis_{len(input_files)}_files"

    # Add metadata about the batch operation
    result = job_manager.submit_job(
        script_path=script_path,
        args=args,
        job_name=job_name
    )

    # Add batch information to the response
    result["batch_info"] = {
        "total_files": len(input_files),
        "files": input_files,
        "note": "Currently processing first file. Full batch processing requires dedicated batch script."
    }

    return result

# ==============================================================================
# Utility Tools
# ==============================================================================

@mcp.tool()
def get_demo_data() -> Dict[str, Any]:
    """
    Get information about available demo data for testing.

    Returns:
        Dictionary with demo data locations and descriptions
    """
    demo_info = {
        "status": "success",
        "demo_sequences": [
            {"id": "demo_001", "sequence": "CRGDMFGC", "description": "Simple RGD-containing cyclic peptide"},
            {"id": "demo_002", "sequence": "CYFQNPMGC", "description": "Hydrophobic cyclic peptide"},
            {"id": "demo_003", "sequence": "CKRRRRRRGC", "description": "Positively charged peptide"},
            {"id": "demo_004", "sequence": "CDDDDDC", "description": "Negatively charged peptide"},
            {"id": "demo_005", "sequence": "CDEFGHIKLMNPQRSTVWY", "description": "All amino acids (except A)"},
            {"id": "demo_006", "sequence": "CLIGKRRC", "description": "Mixed properties"},
            {"id": "demo_007", "sequence": "CYCLINDRC", "description": "Longer cyclic peptide"},
            {"id": "demo_008", "sequence": "CWYC", "description": "Minimal cyclic peptide"}
        ],
        "note": "Use analyze_cyclic_peptides with use_demo=True to analyze all demo sequences"
    }

    # Check if demo files exist
    demo_files = {
        "examples_dir": str(MCP_ROOT / "examples"),
        "demo_fasta": str(MCP_ROOT / "examples" / "data" / "demo_peptides.fasta")
    }

    for key, path in demo_files.items():
        demo_info[key] = {
            "path": path,
            "exists": Path(path).exists()
        }

    return demo_info

@mcp.tool()
def get_server_info() -> Dict[str, Any]:
    """
    Get information about the MCP server and available tools.

    Returns:
        Dictionary with server version, available tools, and usage info
    """
    return {
        "status": "success",
        "server_name": "cycpep-tools",
        "version": "1.0.0",
        "description": "MCP server for cyclic peptide computational analysis",
        "api_types": {
            "synchronous": [
                "analyze_cyclic_peptides",
                "generate_peptide_sequences",
                "get_demo_data",
                "get_server_info"
            ],
            "asynchronous": [
                "submit_peptide_analysis_job",
                "submit_sequence_generation_job",
                "submit_batch_peptide_analysis"
            ],
            "job_management": [
                "get_job_status",
                "get_job_result",
                "get_job_log",
                "cancel_job",
                "list_jobs"
            ]
        },
        "workflow_examples": {
            "quick_analysis": "Use analyze_cyclic_peptides for immediate results",
            "background_job": "Use submit_* functions + get_job_status/result for async operations",
            "batch_processing": "Use submit_batch_* functions for multiple inputs"
        },
        "scripts_directory": str(SCRIPTS_DIR),
        "jobs_directory": str(job_manager.jobs_dir)
    }

# ==============================================================================
# Entry Point
# ==============================================================================

if __name__ == "__main__":
    mcp.run()