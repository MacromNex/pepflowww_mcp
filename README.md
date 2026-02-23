# PepFlowww MCP

> Cyclic peptide computational analysis tools - MCP server for fast peptide property calculation, sequence generation, and analysis

## Table of Contents
- [Overview](#overview)
- [Installation](#installation)
- [Local Usage (Scripts)](#local-usage-scripts)
- [MCP Server Installation](#mcp-server-installation)
- [Using with Claude Code](#using-with-claude-code)
- [Using with Gemini CLI](#using-with-gemini-cli)
- [Available Tools](#available-tools)
- [Examples](#examples)
- [Demo Data](#demo-data)
- [Configuration Files](#configuration-files)
- [Troubleshooting](#troubleshooting)
- [Development](#development)

## Overview

PepFlowww MCP provides fast, reliable tools for cyclic peptide computational analysis. Built on statistical methods rather than deep learning for maximum speed and reliability, this MCP server enables immediate analysis of peptide properties, sequence generation, and drug-likeness assessment.

### Features
- **Fast Property Calculation**: Molecular weight, LogP, TPSA, charge, and drug-likeness (~2 seconds for 8 peptides)
- **Statistical Sequence Generation**: Generate diverse cyclic peptides with customizable constraints (~0.1 seconds for 10 sequences)
- **Comprehensive Analysis**: Amino acid composition, physicochemical properties, and visualization
- **Batch Processing**: Async job submission for large-scale analysis
- **No GPU Required**: CPU-only operation with minimal dependencies

### Directory Structure
```
./
├── README.md               # This file
├── env/                    # Conda environment
├── src/
│   ├── server.py           # MCP server (12 tools)
│   └── jobs/               # Job management system
│       └── manager.py      # Background job processing
├── scripts/
│   ├── analyze_peptides.py # Peptide property analysis
│   ├── generate_sequences.py # Statistical sequence generation
│   └── lib/                # Shared utilities
│       ├── constants.py    # Amino acid properties and definitions
│       ├── io.py          # File I/O utilities for FASTA, CSV
│       ├── validation.py  # Sequence and config validation
│       └── utils.py       # Analysis and manipulation utilities
├── examples/
│   └── data/               # Demo data
│       ├── sequences/      # Sample cyclic peptide sequences
│       │   ├── demo_cyclic_peptides.fasta # 8 demo sequences
│       │   └── demo_peptides.fasta       # Additional samples
│       └── structures/     # Sample 3D structures
│           └── demo_peptide_receptor.pdb
├── configs/                # Configuration files
│   ├── analyze_peptides_config.json   # Analysis parameters
│   └── generate_sequences_config.json # Generation parameters
├── jobs/                   # Job state persistence
└── repo/                   # Original PepFlowww repository
```

---

## Installation

### Quick Setup

Run the automated setup script:

```bash
./quick_setup.sh
```

This will create the environment and install all dependencies automatically.

### Manual Setup (Advanced)

For manual installation or customization, follow these steps.

#### Prerequisites
- Conda or Mamba (mamba recommended for faster installation)
- Python 3.10+
- ~5GB disk space for environment

#### Create Environment
Please strictly follow the information in `reports/step3_environment.md` for detailed setup procedures. A typical workflow is shown below:

```bash
# Navigate to the MCP directory
cd /home/xux/Desktop/CycPepMCP/CycPepMCP/tool-mcps/pepflowww_mcp

# Create conda environment (use mamba if available)
mamba create -p ./env python=3.10 -y
# or: conda create -p ./env python=3.10 -y

# Activate environment
mamba activate ./env
# or: conda activate ./env

# Install from environment.yml (includes scientific stack)
mamba env update -p ./env -f repo/PepFlowww/environment.yml

# Install additional dependencies
pip install joblib lmdb easydict
pip install fastmcp loguru --ignore-installed
```

**Alternative Quick Install (Essential Only):**
```bash
# For minimal installation
mamba create -p ./env python=3.10 numpy pandas matplotlib biopython -y
mamba activate ./env
pip install fastmcp loguru
```

---

## Local Usage (Scripts)

You can use the scripts directly without MCP for local processing.

### Available Scripts

| Script | Description | Runtime | Example |
|--------|-------------|---------|---------|
| `scripts/analyze_peptides.py` | Analyze sequences for properties and drug-likeness | ~2 seconds | See below |
| `scripts/generate_sequences.py` | Generate peptide sequences with constraints | ~0.1 seconds | See below |

### Script Examples

#### Analyze Cyclic Peptides

```bash
# Activate environment
mamba activate ./env

# Analyze demo sequences (8 built-in peptides)
python scripts/analyze_peptides.py --demo --output results/analysis

# Analyze single sequence
python scripts/analyze_peptides.py \
  --sequence "CRGDMFGC" \
  --output results/single_analysis

# Analyze FASTA file
python scripts/analyze_peptides.py \
  --input examples/data/sequences/demo_cyclic_peptides.fasta \
  --output results/file_analysis

# Fast analysis without visualizations
python scripts/analyze_peptides.py --demo --output results/fast --no-viz
```

**Parameters:**
- `--input, -i`: Input FASTA file path
- `--sequence, -s`: Single sequence to analyze
- `--demo`: Use built-in demo sequences (8 peptides)
- `--output, -o`: Output directory (default: results/)
- `--no-viz`: Skip visualizations for faster execution
- `--config`: Custom configuration file

**Expected Output:**
- `composition.csv`: Amino acid composition analysis
- `properties.csv`: Physicochemical properties (MW, LogP, TPSA, etc.)
- `druggability.csv`: Drug-likeness assessment
- `*_distribution.png`: Property visualization plots
- `analysis_summary.txt`: Summary statistics

#### Generate Peptide Sequences

```bash
# Generate 10 sequences with default settings
python scripts/generate_sequences.py \
  --num_samples 10 \
  --output results/generated.fasta

# Generate with specific length
python scripts/generate_sequences.py \
  --num_samples 5 \
  --length 12 \
  --output results/length12.fasta

# Use natural amino acid frequencies
python scripts/generate_sequences.py \
  --num_samples 8 \
  --weights natural \
  --output results/natural_freq.fasta

# Generate CSV with metadata
python scripts/generate_sequences.py \
  --num_samples 10 \
  --format csv \
  --output results/sequences.csv

# No cysteines or charge balancing
python scripts/generate_sequences.py \
  --num_samples 10 \
  --no-cysteines \
  --no-balance \
  --output results/simple.fasta
```

**Parameters:**
- `--num_samples, -n`: Number of sequences to generate
- `--length, -l`: Fixed sequence length (default: random 6-15)
- `--weights, -w`: Amino acid weights ('uniform' or 'natural')
- `--format, -f`: Output format ('fasta' or 'csv')
- `--output, -o`: Output file path
- `--no-cysteines`: Exclude cysteine residues
- `--no-balance`: Skip charge balancing

---

## MCP Server Installation

### Option 1: Using fastmcp (Recommended)

```bash
# Install MCP server for Claude Code
fastmcp install src/server.py --name pepflowww-tools
```

### Option 2: Manual Installation for Claude Code

```bash
# Add MCP server to Claude Code
claude mcp add pepflowww-tools -- $(pwd)/env/bin/python $(pwd)/src/server.py

# Verify installation
claude mcp list
```

### Option 3: Configure in settings.json

Add to `~/.claude/settings.json`:

```json
{
  "mcpServers": {
    "pepflowww-tools": {
      "command": "/home/xux/Desktop/CycPepMCP/CycPepMCP/tool-mcps/pepflowww_mcp/env/bin/python",
      "args": ["/home/xux/Desktop/CycPepMCP/CycPepMCP/tool-mcps/pepflowww_mcp/src/server.py"]
    }
  }
}
```

### Start Server for Testing

```bash
# Activate environment
mamba activate ./env

# Development mode (with FastMCP inspector)
fastmcp dev src/server.py

# Production mode (stdio transport)
python src/server.py
```

---

## Using with Claude Code

After installing the MCP server, you can use it directly in Claude Code.

### Quick Start

```bash
# Start Claude Code
claude
```

### Example Prompts

#### Tool Discovery
```
What tools are available from pepflowww-tools?
```

#### Fast Property Calculation (Sync API)
```
Calculate molecular properties for this cyclic peptide: CRGDMFGC
```

#### Demo Data Analysis
```
Analyze all the demo peptides for drug-likeness properties
```

#### Sequence Generation (Sync API)
```
Generate 5 cyclic peptides with length 10 using natural amino acid frequencies
```

#### Background Job Submission (Async API)
```
Submit a background job to analyze @examples/data/sequences/demo_cyclic_peptides.fasta with visualizations
```

#### Job Management
```
Check the status of job abc12345
```

#### Batch Processing
```
Analyze these files in batch:
- @examples/data/sequences/demo_cyclic_peptides.fasta
- @examples/data/sequences/demo_peptides.fasta
```

### Using @ References

In Claude Code, use `@` to reference files and directories:

| Reference | Description |
|-----------|-------------|
| `@examples/data/sequences/demo_cyclic_peptides.fasta` | Reference the main demo FASTA file |
| `@configs/analyze_peptides_config.json` | Reference analysis configuration |
| `@results/` | Reference output directory |
| `@scripts/analyze_peptides.py` | Reference script files |

---

## Using with Gemini CLI

### Configuration

Add to `~/.gemini/settings.json`:

```json
{
  "mcpServers": {
    "pepflowww-tools": {
      "command": "/home/xux/Desktop/CycPepMCP/CycPepMCP/tool-mcps/pepflowww_mcp/env/bin/python",
      "args": ["/home/xux/Desktop/CycPepMCP/CycPepMCP/tool-mcps/pepflowww_mcp/src/server.py"]
    }
  }
}
```

### Example Prompts

```bash
# Start Gemini CLI
gemini

# Example prompts (same as Claude Code)
> What cyclic peptide tools are available?
> Calculate properties for cyclic peptide CRGDMFGC
> Generate 10 diverse cyclic peptides with drug-like properties
```

---

## Available Tools

### Quick Operations (Sync API)

These tools return results immediately (< 10 seconds):

| Tool | Description | Parameters | Runtime |
|------|-------------|------------|---------|
| `analyze_cyclic_peptides` | Calculate molecular properties, drug-likeness | `input_file`, `sequence`, `use_demo`, `output_file`, `include_visualizations`, `include_druggability`, `no_viz` | ~2 seconds |
| `generate_peptide_sequences` | Generate sequences with constraints | `num_samples`, `output_file`, `sequence_length`, `amino_acid_weights`, `include_cysteines`, `charged_balance`, `output_format` | ~0.1 seconds |
| `get_demo_data` | List available demo data | None | Instant |
| `get_server_info` | Server and tool information | None | Instant |

### Long-Running Tasks (Submit API)

These tools return a job_id for tracking background operations:

| Tool | Description | Use Case |
|------|-------------|----------|
| `submit_peptide_analysis_job` | Background peptide analysis | Large datasets, demonstration |
| `submit_sequence_generation_job` | Background sequence generation | Large batch generation |
| `submit_batch_peptide_analysis` | Process multiple FASTA files | Multi-file workflows |

### Job Management Tools

| Tool | Description | Returns |
|------|-------------|---------|
| `get_job_status` | Check job progress | Status, timestamps, progress |
| `get_job_result` | Get completed results | Full results with output files |
| `get_job_log` | View execution logs | Log lines and total count |
| `cancel_job` | Cancel running job | Success/error message |
| `list_jobs` | List all jobs | Array of jobs with status filter |

---

## Examples

### Example 1: Quick Property Calculation

**Goal:** Calculate drug-like properties for a cyclic peptide

**Using Script:**
```bash
python scripts/analyze_peptides.py \
  --sequence "CRGDMFGC" \
  --output results/single_peptide
```

**Using MCP (in Claude Code):**
```
Calculate molecular properties for CRGDMFGC including molecular weight, logP, and TPSA. Show drug-likeness assessment.
```

**Expected Output:**
- Molecular weight: ~951 Da
- LogP: Hydrophobicity index
- TPSA: Topological polar surface area
- Drug-likeness score: 0.0-1.0 scale
- Charge at pH 7
- Amino acid composition breakdown

### Example 2: Demo Data Analysis

**Goal:** Analyze all demo sequences for comprehensive properties

**Using Script:**
```bash
python scripts/analyze_peptides.py \
  --demo \
  --output results/demo_analysis
```

**Using MCP (in Claude Code):**
```
Analyze all demo peptide sequences for drug-likeness. Generate visualizations showing property distributions and identify the most promising candidates.
```

**Expected Analysis:** 8 demo sequences including:
- `antimicrobial_cyclic_1`: CKWYFWKRK
- `therapeutic_candidate`: ACDEFGHIKC
- `cell_penetrating_cyclic`: RRRQRRKRG
- Property distributions across all sequences
- Drug-likeness rankings

### Example 3: Sequence Generation with Constraints

**Goal:** Generate drug-like cyclic peptides with specific properties

**Using Script:**
```bash
python scripts/generate_sequences.py \
  --num_samples 10 \
  --length 12 \
  --weights natural \
  --output results/druglike.fasta
```

**Using MCP (in Claude Code):**
```
Generate 10 cyclic peptides with length 12 using natural amino acid frequencies. Include cysteines for cyclization and balance charges for stability.
```

**Expected Output:**
- 10 sequences with exactly 12 amino acids
- Natural frequency distribution
- Balanced positive/negative charges
- Cysteine residues for cyclization

### Example 4: Background Job Workflow

**Goal:** Process large dataset in background with progress monitoring

**Using MCP (in Claude Code):**
```
Submit a background job to analyze @examples/data/sequences/demo_cyclic_peptides.fasta with full visualizations and drug-likeness assessment. Name the job "demo_analysis".
```

**Workflow:**
1. `submit_peptide_analysis_job` → Returns job_id
2. `get_job_status(job_id)` → Monitor progress
3. `get_job_result(job_id)` → Get results when complete
4. `get_job_log(job_id)` → View execution details

### Example 5: Virtual Screening Pipeline

**Goal:** Screen peptides for oral bioavailability

**Using MCP (in Claude Code):**
```
I want to screen these cyclic peptides for oral bioavailability:
1. CRGDMFGC
2. CYFQNPMGC
3. CKRRRRRRGC

Calculate properties for all of them and identify which ones have:
- Molecular weight < 1000 Da
- LogP between -2 and 5
- TPSA < 250 Ų
- Absolute charge ≤ 2
```

---

## Demo Data

The `examples/data/` directory contains sample data for testing:

| File | Description | Sequences | Use With |
|------|-------------|-----------|----------|
| `sequences/demo_cyclic_peptides.fasta` | Main demo dataset | 8 diverse peptides | All analysis tools |
| `sequences/demo_peptides.fasta` | Additional samples | Various lengths | Property comparison |
| `structures/demo_peptide_receptor.pdb` | 3D structure example | PDB format | Future structure tools |

### Demo Sequences Overview

| ID | Sequence | Length | Type | Properties |
|----|----------|--------|------|------------|
| `antimicrobial_cyclic_1` | CKWYFWKRK | 9 | Antimicrobial | High positive charge |
| `antimicrobial_cyclic_2` | CWRFWCGFRC | 10 | Antimicrobial | Aromatic-rich |
| `cell_penetrating_cyclic` | RRRQRRKRG | 9 | Cell penetrating | Multiple arginines |
| `therapeutic_candidate` | ACDEFGHIKC | 10 | Drug candidate | Diverse properties |
| `natural_product_mimic` | YFGHWKLVC | 9 | Natural mimic | Hydrophobic bias |
| `designed_binder` | ALTDHENVC | 9 | Binding peptide | Balanced composition |
| `cyclic_control` | GFPSWQNMC | 9 | Control sequence | Moderate properties |
| `linear_control` | GPGPGPGPGP | 10 | Linear control | No cyclization |

---

## Configuration Files

The `configs/` directory contains configuration templates:

### analyze_peptides_config.json
```json
{
  "analysis": {
    "include_composition": true,
    "include_properties": true,
    "include_druggability": true
  },
  "visualization": {
    "include_visualizations": true,
    "plot_dpi": 300
  },
  "druggability_criteria": {
    "max_molecular_weight": 2000,
    "max_absolute_charge": 3,
    "hydrophobicity_range": [-2.0, 2.0]
  }
}
```

### generate_sequences_config.json
```json
{
  "generation": {
    "sequence_length_range": [6, 15],
    "amino_acid_weights": "uniform"
  },
  "composition": {
    "include_cysteines": true,
    "charged_balance": true
  },
  "constraints": {
    "max_charge_imbalance": 3,
    "min_hydrophobic_ratio": 0.2
  }
}
```

### Customizing Configurations

```bash
# Copy default config
cp configs/analyze_peptides_config.json configs/my_analysis.json

# Edit parameters
nano configs/my_analysis.json

# Use custom config
python scripts/analyze_peptides.py --demo --config configs/my_analysis.json
```

---

## Troubleshooting

### Environment Issues

**Problem:** Environment not found
```bash
# Recreate environment
mamba create -p ./env python=3.10 -y
mamba activate ./env
pip install numpy pandas matplotlib fastmcp loguru
```

**Problem:** Import errors
```bash
# Verify key packages
python -c "import numpy, pandas, matplotlib; print('Essential packages OK')"
python -c "import fastmcp; print('FastMCP OK')"
```

**Problem:** matplotlib backend issues (headless systems)
```bash
# Set non-interactive backend
export MPLBACKEND=Agg
python scripts/analyze_peptides.py --demo --output results/
```

### MCP Issues

**Problem:** Server not found in Claude Code
```bash
# Check MCP registration
claude mcp list

# Re-add if needed
claude mcp remove pepflowww-tools
claude mcp add pepflowww-tools -- $(pwd)/env/bin/python $(pwd)/src/server.py
```

**Problem:** Tools not working
```bash
# Test server directly
python -c "
from src.server import mcp
tools = list(mcp.list_tools().keys())
print(f'Available tools: {len(tools)}')
print('\\n'.join(tools))
"
```

**Problem:** Invalid sequence error
```
Ensure your sequences contain only standard amino acids (ACDEFGHIKLMNPQRSTVWY).
For cyclic peptides, include cysteines (C) for disulfide cyclization or use head-to-tail notation.
```

### Job Issues

**Problem:** Job stuck in pending
```bash
# Check job directory
ls -la jobs/

# View recent job logs
find jobs/ -name "*.log" -exec tail -5 {} \;
```

**Problem:** Job failed
```
Use get_job_log with job_id and tail=100 to see detailed error messages.
Most common issues:
- Invalid input file paths
- Insufficient disk space
- Memory limitations
```

### Performance Issues

**Problem:** Slow analysis
```bash
# Skip visualizations for faster execution
python scripts/analyze_peptides.py --demo --no-viz --output results/

# Or use sync API in MCP
analyze_cyclic_peptides(use_demo=True, no_viz=True)
```

### File Path Issues

**Problem:** File not found
```bash
# Check file exists
ls -la examples/data/sequences/demo_cyclic_peptides.fasta

# Use absolute paths
python scripts/analyze_peptides.py \
  --input $(pwd)/examples/data/sequences/demo_cyclic_peptides.fasta
```

---

## Development

### Running Tests

```bash
# Activate environment
mamba activate ./env

# Test scripts independently
python scripts/analyze_peptides.py --demo --output test_results/
python scripts/generate_sequences.py --num_samples 3 --output test_sequences.fasta

# Test MCP server
fastmcp dev src/server.py
```

### Server Architecture

```
src/
├── server.py              # FastMCP server with 12 tools
├── jobs/                  # Job management system
│   └── manager.py         # Background job execution
└── utils/                 # Future utilities

jobs/                      # Persistent job storage
└── <job_id>/
    ├── metadata.json      # Job status and parameters
    ├── job.log           # Execution logs
    └── output*           # Generated files
```

### Adding New Tools

```python
# In src/server.py
@mcp.tool()
def new_analysis_tool(input_param: str) -> Dict[str, Any]:
    """Description of what the tool does."""
    try:
        # Import script function
        from new_script import run_analysis

        result = run_analysis(input_param)
        return {"status": "success", **result}
    except Exception as e:
        return {"status": "error", "error": str(e)}
```

### Performance Monitoring

```bash
# Check memory usage
python -c "
import psutil
import os
print(f'Memory: {psutil.Process(os.getpid()).memory_info().rss / 1024**2:.1f} MB')
"

# Check execution time
time python scripts/analyze_peptides.py --demo --output /tmp/test
```

---

## License

Based on [PepFlowww](https://github.com/riacd/PepFlowww) - Original deep learning framework for peptide design

## Credits

- **Original Repository**: PepFlowww by riacd - Full-Atom Peptide Design based on Multi-modal Flow Matching
- **MCP Implementation**: Statistical analysis and sequence generation tools
- **FastMCP Framework**: Anthropic's Model Context Protocol implementation
- **Dependencies**: NumPy, Pandas, Matplotlib for core computational capabilities