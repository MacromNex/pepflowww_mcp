# Step 3: Use Cases Report

## Scan Information
- **Scan Date**: 2026-01-01
- **Filter Applied**: peptide structure generation using PepFlowww
- **Repository**: PepFlowww (Full-Atom Peptide Design based on Multi-modal Flow Matching)
- **Python Version**: 3.10.12
- **Environment Strategy**: Single environment

## Repository Analysis

### Source Code Structure
- **Main training script**: `train.py`, `train_ddp.py`
- **Core models**: `models_con/flow_model.py`
- **Sampling**: `models_con/sample.py`
- **Inference**: `models_con/inference.py`
- **Data handling**: `models_con/pep_dataloader.py`
- **Utilities**: `pepflow/` module with geometry, protein handling
- **Evaluation**: `eval/` directory with multiple evaluation scripts
- **Notebooks**: `playgrounds/` with dataset generation and clustering examples

### Key Functionalities Identified
1. **Flow-based generative modeling** for peptide design
2. **Multi-modal generation** (structure + sequence)
3. **Backbone and side-chain** coordinate prediction
4. **Peptide-receptor complex** training and sampling
5. **Structure reconstruction** and validation
6. **Dataset preprocessing** for peptide-receptor pairs

## Use Cases Extracted

### UC-001: Train Flow Model for Peptide Design
- **Description**: Train flow-based generative model for cyclic peptide design using peptide-receptor binding data
- **Script Path**: `examples/use_case_1_train_model.py`
- **Complexity**: Complex
- **Priority**: High
- **Environment**: `./env`
- **Source**: `train.py`, configuration files

**Inputs:**
| Name | Type | Description | Parameter |
|------|------|-------------|----------|
| config | file | YAML configuration file | --config |
| device | string | Computing device (cpu/cuda) | --device |
| max_iters | integer | Maximum training iterations | --max_iters |
| debug | boolean | Debug mode flag | --debug |

**Outputs:**
| Name | Type | Description |
|------|------|-------------|
| checkpoint | file | Trained model checkpoint (.pt) |
| logs | directory | Training logs and metrics |

**Example Usage:**
```bash
python examples/use_case_1_train_model.py --config configs/learn_angle.yaml --device cpu --max_iters 100
```

**Example Data**: Demo configuration in `examples/data/config_demo.yaml`

---

### UC-002: Sample New Peptides
- **Description**: Generate diverse cyclic peptides using trained flow model given receptor binding pocket
- **Script Path**: `examples/use_case_2_sample_peptides.py`
- **Complexity**: Medium
- **Priority**: High
- **Environment**: `./env`
- **Source**: `models_con/sample.py`, `models_con/inference.py`

**Inputs:**
| Name | Type | Description | Parameter |
|------|------|-------------|----------|
| model | file | Trained model checkpoint | --model |
| num_samples | integer | Number of peptides to generate | --num_samples |
| num_steps | integer | Diffusion sampling steps | --num_steps |
| peptide_length | integer | Target peptide length | --peptide_length |
| output | directory | Output directory | --output |

**Outputs:**
| Name | Type | Description |
|------|------|-------------|
| structures | files | Generated peptide PDB files |
| sequences | files | Generated sequences (FASTA) |

**Example Usage:**
```bash
python examples/use_case_2_sample_peptides.py --num_samples 8 --num_steps 50 --output generated_peptides/
```

**Example Data**: Auto-generated demo data for receptor context

---

### UC-003: Structure Inference and Reconstruction
- **Description**: Predict 3D peptide structure from amino acid sequence using flow model
- **Script Path**: `examples/use_case_3_structure_inference.py`
- **Complexity**: Medium
- **Priority**: High
- **Environment**: `./env`
- **Source**: `models_con/inference.py`, geometry reconstruction utilities

**Inputs:**
| Name | Type | Description | Parameter |
|------|------|-------------|----------|
| sequence | string | Peptide amino acid sequence | --sequence |
| fasta | file | FASTA file with sequence | --fasta |
| model | file | Trained model checkpoint | --model |
| num_steps | integer | Inference steps | --num_steps |
| include_sidechain | boolean | Include side-chain atoms | --include_sidechain |

**Outputs:**
| Name | Type | Description |
|------|------|-------------|
| structure | file | Predicted PDB structure |
| multiple_samples | files | Alternative conformations |

**Example Usage:**
```bash
python examples/use_case_3_structure_inference.py --sequence "CYCLIGKRC" --output predicted_structure.pdb
```

**Example Data**: Built-in demo sequences for testing

---

### UC-004: Protein Structure Parsing
- **Description**: Parse and preprocess protein/peptide structures for training or analysis
- **Script Path**: `examples/use_case_4_structure_parsing.py`
- **Complexity**: Medium
- **Priority**: Medium
- **Environment**: `./env`
- **Source**: `pepflow/modules/protein/parsers.py`, `playgrounds/gen_dataset.ipynb`

**Inputs:**
| Name | Type | Description | Parameter |
|------|------|-------------|----------|
| pdb | file | Input PDB structure file | --pdb |
| max_peptide_length | integer | Max length to classify as peptide | --max_peptide_length |
| interface_cutoff | float | Distance cutoff for binding interface | --interface_cutoff |
| create_demo | boolean | Create demo structure | --create_demo |

**Outputs:**
| Name | Type | Description |
|------|------|-------------|
| sequences | file | Extracted sequences (FASTA) |
| interface_analysis | file | Binding interface analysis |
| summary | file | Structure processing summary |

**Example Usage:**
```bash
python examples/use_case_4_structure_parsing.py --create_demo --output structure_analysis/
```

**Example Data**: Auto-generated demo PDB structure

---

### UC-005: Peptide Sequence Analysis
- **Description**: Analyze peptide sequences for composition, properties, and drug-likeness
- **Script Path**: `examples/use_case_5_peptide_analysis.py`
- **Complexity**: Simple
- **Priority**: Medium
- **Environment**: `./env`
- **Source**: `data/residue_constants.py`, custom analysis utilities

**Inputs:**
| Name | Type | Description | Parameter |
|------|------|-------------|----------|
| sequences | file | FASTA file with sequences | --sequences |
| sequence | string | Single sequence to analyze | --sequence |
| create_demo | boolean | Use demo sequences | --create_demo |
| output | directory | Output directory | --output |

**Outputs:**
| Name | Type | Description |
|------|------|-------------|
| composition | file | Amino acid composition analysis (CSV) |
| properties | file | Physicochemical properties (CSV) |
| druggability | file | Drug-likeness assessment (CSV) |
| visualizations | directory | Analysis plots and charts |

**Example Usage:**
```bash
python examples/use_case_5_peptide_analysis.py --create_demo --output peptide_analysis/
```

**Example Data**: Demo cyclic peptide sequences in `examples/data/sequences/`

---

## Additional Utilities

### Complete Workflow Script
- **Description**: Run all use cases in sequence for demonstration
- **Script Path**: `examples/run_all_examples.py`
- **Usage**: `python examples/run_all_examples.py --quick`

## Summary

| Metric | Count |
|--------|-------|
| Total Use Cases Found | 5 |
| Scripts Created | 6 (including workflow script) |
| High Priority | 3 |
| Medium Priority | 2 |
| Low Priority | 0 |
| Demo Data Created | Yes |

## Use Case Classification by Functionality

### Core Flow Model Operations (3 use cases)
- **UC-001**: Model Training - Essential for creating peptide design models
- **UC-002**: Peptide Sampling - Primary application for generating new peptides
- **UC-003**: Structure Inference - Structure prediction from sequence

### Data Processing and Analysis (2 use cases)
- **UC-004**: Structure Parsing - Preprocessing pipeline for training data
- **UC-005**: Sequence Analysis - Property analysis and characterization

## Demo Data Index

| Source | Destination | Description |
|--------|-------------|-------------|
| Generated | `examples/data/sequences/demo_cyclic_peptides.fasta` | 8 demo peptide sequences |
| Generated | `examples/data/config_demo.yaml` | Minimal model configuration |
| Auto-created | `examples/data/structures/demo_peptide_receptor.pdb` | Demo PDB structure |

## Implementation Notes

### Key Features Implemented
1. **Standalone Scripts**: Each use case is a complete, runnable script
2. **Error Handling**: Graceful handling of missing dependencies/data
3. **Demo Mode**: All scripts can run without real training data
4. **Command-Line Interface**: Full argparse support with help
5. **Documentation**: Comprehensive docstrings and usage examples

### Design Principles
1. **Self-Contained**: Scripts work independently without external dependencies
2. **Educational**: Clear documentation of each step for learning
3. **Flexible**: Configurable parameters for different use cases
4. **Robust**: Error handling for missing files or failed operations

### Integration with PepFlowww
- Scripts use original PepFlowww modules via Python path
- Maintain compatibility with existing data formats
- Leverage existing utilities for geometry and protein handling
- Support both CPU and GPU execution modes

## Next Steps for MCP Integration

1. **Server Implementation**: Create MCP server wrapper for use cases
2. **API Design**: Define MCP tools for each use case
3. **Data Flow**: Standardize input/output formats for MCP
4. **Error Handling**: Implement robust error reporting for MCP clients
5. **Documentation**: Create MCP-specific usage documentation

## Validation Status

- [x] All scripts created and syntax-validated
- [x] Demo data generated and accessible
- [x] Scripts can run in demo mode without real data
- [x] Command-line interfaces implemented
- [x] Documentation and examples complete
- [x] Integration with PepFlowww modules verified