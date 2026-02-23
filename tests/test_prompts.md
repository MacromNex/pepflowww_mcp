# MCP Integration Test Prompts for PepFlowww Tools

## Tool Discovery Tests

### Prompt 1: List All Tools
"What MCP tools are available for cyclic peptides? Give me a brief description of each."

**Expected Behavior:**
- Should list all 12 tools from pepflowww-tools server
- Should categorize them as Sync, Async, and Job Management tools
- Should provide clear descriptions for each tool

### Prompt 2: Tool Details
"Explain how to use the analyze_cyclic_peptides tool, including all parameters and what it returns."

**Expected Behavior:**
- Should show tool signature and parameter details
- Should explain input formats (sequences, use_demo flag, etc.)
- Should describe output format and structure

### Prompt 3: Server Information
"Use get_server_info to show me the capabilities of the pepflowww-tools server."

**Expected Behavior:**
- Should return server metadata including name, version
- Should list all available tool categories
- Should show configuration information

## Sync Tool Tests

### Prompt 4: Property Calculation with Demo Data
"Use analyze_cyclic_peptides with demo data to show me peptide properties."

**Expected Behavior:**
- Should execute within 10 seconds
- Should return structured results with properties like molecular weight, charge
- Should include amino acid composition analysis
- Should show druggability assessment

### Prompt 5: Sequence Generation
"Generate 5 cyclic peptides with length 8-12 amino acids, balanced charge, and hydrophobic bias."

**Expected Behavior:**
- Should execute within 5 seconds
- Should return exactly 5 sequences
- Should meet length constraints
- Should include metadata (length, charge, hydrophobicity)

### Prompt 6: Get Demo Data
"Show me what demo peptides are available using get_demo_data."

**Expected Behavior:**
- Should return 8 demo peptide sequences
- Should include sequence names and properties
- Should format nicely for display

### Prompt 7: Error Handling - Invalid Parameters
"Try to analyze peptides with invalid parameters: use_demo=false but no sequences provided."

**Expected Behavior:**
- Should return clear error message
- Should not crash the server
- Should suggest correct usage

## Submit API Tests

### Prompt 8: Submit Analysis Job
"Submit a background job to analyze cyclic peptides using demo data. Name it 'demo-analysis-test'."

**Expected Behavior:**
```json
{
  "status": "submitted",
  "job_id": "abc12345",
  "message": "Job submitted. Use get_job_status('abc12345') to check progress."
}
```

### Prompt 9: Check Job Status
"Check the status of job abc12345."

**Expected Behavior:**
```json
{
  "job_id": "abc12345",
  "status": "running|completed|failed",
  "submitted_at": "2024-01-01T12:00:00",
  "job_name": "demo-analysis-test"
}
```

### Prompt 10: Get Job Results
"Get the results for completed job abc12345."

**Expected Behavior:**
```json
{
  "status": "success",
  "result": {
    "properties": [...],
    "composition": [...],
    "visualizations": [...]
  }
}
```

### Prompt 11: View Job Logs
"Show me the last 30 lines of logs for job abc12345."

**Expected Behavior:**
- Should show execution logs
- Should include timestamps
- Should show any errors or warnings

### Prompt 12: List All Jobs
"List all submitted jobs with status 'completed'."

**Expected Behavior:**
- Should show jobs filtered by status
- Should include job_id, name, timestamps
- Should be sorted by submission time

### Prompt 13: Submit Generation Job
"Submit a background job to generate 50 cyclic peptides with length 6-10, natural amino acid distribution."

**Expected Behavior:**
- Should accept large batch size
- Should return job_id for tracking
- Should handle longer processing time gracefully

## Batch Processing Tests

### Prompt 14: Batch Analysis (Multiple Files)
"Run batch peptide analysis on demo sequences - process them as separate files."

**Expected Behavior:**
- Should process multiple input files
- Should return batch job ID
- Should track progress across all files

### Prompt 15: Batch Status Check
"Check the status and progress of batch job <batch_job_id>."

**Expected Behavior:**
- Should show overall batch progress
- Should indicate how many files are processed
- Should show any failed individual jobs

## End-to-End Scenarios

### Prompt 16: Full Workflow - Single Peptide
"For the cyclic peptide sequence GRGDSP:
1. First analyze its properties
2. Generate 5 similar sequences with comparable properties
3. Analyze the generated sequences
Summarize all results."

**Expected Behavior:**
- Should execute sequence of related operations
- Should pass data between operations appropriately
- Should provide comprehensive summary

### Prompt 17: Drug Discovery Pipeline
"I want to screen cyclic peptides for drug-likeness:
1. Use demo data to analyze properties
2. Identify peptides with MW < 1000 Da and favorable charge
3. Generate 10 new sequences with similar properties
Show me the final candidates."

**Expected Behavior:**
- Should filter based on drug-like properties
- Should use filtering results to guide generation
- Should present final candidates clearly

### Prompt 18: Research Workflow
"Submit jobs to:
1. Analyze demo peptides (background job)
2. Generate 25 new sequences (background job)
While they run, check their progress periodically.
When done, compare the generated vs demo peptide properties."

**Expected Behavior:**
- Should handle multiple concurrent background jobs
- Should allow progress monitoring
- Should enable results comparison

### Prompt 19: Quality Control Scenario
"Generate 10 sequences, then:
1. Validate they are proper cyclic peptides
2. Check for any unusual amino acid compositions
3. Flag any that might have synthesis issues
Provide a quality report."

**Expected Behavior:**
- Should validate sequence format and cyclization
- Should identify composition outliers
- Should assess synthesizability

### Prompt 20: Permeability Assessment
"I need to assess membrane permeability potential:
1. Analyze demo peptides for relevant properties
2. Generate peptides optimized for permeability
3. Compare hydrophobicity and charge distributions
Recommend the best candidates."

**Expected Behavior:**
- Should focus on permeability-relevant properties
- Should optimize generation parameters accordingly
- Should provide clear recommendations

## Error Handling and Edge Cases

### Prompt 21: Large Batch Processing
"Submit a job to generate 500 cyclic peptides with complex constraints."

**Expected Behavior:**
- Should handle large requests gracefully
- Should provide realistic time estimates
- Should allow progress monitoring

### Prompt 22: Invalid Job Operations
"Try to get results for a non-existent job ID: 'invalid-job-123'."

**Expected Behavior:**
- Should return clear error message
- Should suggest how to list valid job IDs
- Should not crash

### Prompt 23: Cancel Running Job
"Cancel the currently running job xyz98765."

**Expected Behavior:**
- Should stop job execution cleanly
- Should update job status to cancelled
- Should free up system resources

### Prompt 24: Concurrent Job Limits
"Submit 5 analysis jobs simultaneously and monitor their execution."

**Expected Behavior:**
- Should handle multiple concurrent jobs
- Should queue appropriately if limits are reached
- Should provide clear status for each job

### Prompt 25: System Resource Monitoring
"Check server status and resource usage while running multiple jobs."

**Expected Behavior:**
- Should provide server health information
- Should show resource utilization
- Should warn if approaching limits

## Integration Testing Notes

### Success Criteria for Each Test:
- **Response Time:** Sync tools < 30 seconds, async job submission < 5 seconds
- **Data Accuracy:** Results match expected chemical/biological validity
- **Error Handling:** Clear, helpful error messages with suggestions
- **Job Management:** Complete workflow from submit → status → results works
- **Resource Management:** No memory leaks or hanging processes

### Test Environment:
- Server: pepflowww-tools (registered in Claude Code)
- Environment: /home/xux/Desktop/CycPepMCP/CycPepMCP/tool-mcps/pepflowww_mcp/env
- Demo Data: Available via get_demo_data tool
- Job Storage: jobs/ directory with persistence

### Common Issues to Watch For:
1. **Path Resolution:** Absolute vs relative paths in job execution
2. **Environment Activation:** Python environment not properly activated
3. **Port Conflicts:** FastMCP dev server port conflicts
4. **Memory Usage:** Large batch jobs consuming excessive memory
5. **File Permissions:** Job output file access issues
6. **Concurrent Access:** Multiple jobs modifying shared resources

### Debugging Commands:
```bash
# Check server registration
claude mcp list

# Monitor job directory
ls -la jobs/

# Check recent job logs
tail -50 jobs/*/job.log

# Test server directly
python -c "from src.server import mcp; print('Server OK')"

# Verify environment
python -c "import pandas, numpy; print('Dependencies OK')"
```