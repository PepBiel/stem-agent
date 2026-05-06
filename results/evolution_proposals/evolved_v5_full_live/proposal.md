# Evolution Proposal: evolved_deep_research_v6

Generated at: `2026-05-06T11:21:54+00:00`
Source run: `results/runs/evolved_deep_research_v5/evolved_v5_full_live`
Base genome: `configs/evolved_deep_research_agent_v5.yaml`
Schema: `configs/genome_schema.yaml`
Dry run: `False`

## Aggregate Signals

| Metric | Value |
|---|---:|
| Heuristic avg | 0.9492 |
| Judge avg | 0.8073 |
| Final avg | 0.8569 |
| Combined tokens | 354487 |

## Per-Question Signals

| Question | Heuristic | Judge | Final | Tags | Recommended fix |
|---|---:|---:|---:|---|---|
| DR-001 | 0.9786 | 0.7083 | 0.8029 | indirect_support, potentially_suspicious_citations, thin_metadata | Replace the generic URL citations with clearly identified, directly relevant sources (titles/authors/years) and ground each failure mode in a specific passage or result rather than broad inference. |
| DR-002 | 0.9625 | 0.8333 | 0.8785 | none | Tighten the tool-use and 'when preferable' statements by separating directly supported facts from inference, and rely more on primary or framework documentation for those trade-offs. |
| DR-003 | 0.9289 | 0.8750 | 0.8939 | weak_source | Tighten the survey-based synthesis by tying each broad trend claim to a more specific, directly supported sentence or table entry, and avoid any unsupported generalizations. |
| DR-004 | 0.8917 | 0.8750 | 0.8808 | lightly_inferential_failure_modes, unsupported_claim, weak_source | Tighten the failure-mode discussion by either citing a source that explicitly discusses agentic-RAG trade-offs or clearly marking the listed failure modes as examples rather than source-backed claims. |
| DR-005 | 1.0000 | 0.8750 | 0.9187 | none | Replace subjective or potentially overstated phrases like 'canonical example' with more precise wording and add one sentence explaining concrete engineering trade-offs and failure modes for each technique. |
| DR-006 | 0.9750 | 0.7500 | 0.8288 | minor_inference_instead_of_direct_support | Replace the inferred role-confusion wording with a directly supported explanation from a source that explicitly discusses role ambiguity, misassignment, or handoff errors in multi-agent systems. |
| DR-007 | 0.8942 | 0.8750 | 0.8817 | unsupported_claim, weak_source | Tighten the evidence for the inference-heavy recommendations by tying each one to a specific passage or by explicitly labeling them as unsourced policy suggestions rather than source-backed facts. |
| DR-008 | 0.9625 | 0.6667 | 0.7702 | limited_depth_on_engineering_tradeoffs, some_claims_are_inferred_not_directly_evidenced, uncertainty_handling_is_generic | Tighten the evidence for each trade-off with source-specific examples or quotes, and separate directly supported claims from engineering inferences. |

## Diagnosed Failure Modes

- Failure tag counts: `{'indirect_support': 1, 'lightly_inferential_failure_modes': 1, 'limited_depth_on_engineering_tradeoffs': 1, 'minor_inference_instead_of_direct_support': 1, 'potentially_suspicious_citations': 1, 'some_claims_are_inferred_not_directly_evidenced': 1, 'thin_metadata': 1, 'uncertainty_handling_is_generic': 1, 'unsupported_claim': 2, 'weak_source': 6}`
- Theme counts: `{'citation_contract': 6, 'cost_grounding': 1, 'failure_examples': 6, 'inference_labeling': 7, 'source_specificity': 6, 'weak_source_discipline': 2}`
- Low judge questions: `['DR-001', 'DR-006', 'DR-008']`
- Low source-quality questions: `['DR-003', 'DR-004', 'DR-007']`
- Unsupported-claim questions: `['DR-004', 'DR-007']`
- Parse-warning questions: `['DR-003']`
- Citation-warning questions: `[]`

## Proposed Genome Changes

### Add a source-specific evidence gate

- Proposal id: `source_specificity_gate`
- Change: Require each evidence-table item to name the exact source finding, metric, or documented behavior it supports.

### Separate direct evidence from engineering inference

- Proposal id: `inference_budget`
- Change: Limit recommendation-style claims unless they explicitly cite the source facts they are inferred from.

### Raise the authoritative-source floor

- Proposal id: `authoritative_source_floor`
- Change: Prefer papers, official docs, and benchmark pages; allow vendor/blog sources only when no primary source covers the same claim.

### Require direct support for cost and latency claims

- Proposal id: `cost_claim_support`
- Change: Treat cost, latency, and token-efficiency claims as high-risk claims requiring a directly cited metric or a clearly labeled mechanism-level inference.

### Ground failure modes in concrete examples

- Proposal id: `failure_mode_examples`
- Change: Ask the answer to provide one sourced example for each named failure mode or explicitly label it as a hypothetical engineering risk.

### Keep the raw-URL citation contract as a rejection gate

- Proposal id: `citation_contract_repair`
- Change: Reject candidate answers with unsupported claim lines, provider citation markers, or rejected-source leakage.

### Keep tolerant JSON recovery and structured-output checks

- Proposal id: `structured_output_repair`
- Change: Recover valid leading JSON objects, then warn when the model output still violates the citation contract.

## Safeguards

- The proposal preserves the existing tool boundary: web search only.
- It does not apply itself automatically.
- The candidate genome must pass schema validation.
- A smoke run should pass before any live batch.
- Acceptance still depends on fixed-set evaluation against the parent.

## Validation

- Attempted: `True`
- Valid: `True`
- Errors: `[]`
- Warnings: `[]`

## Expected Artifacts

- Proposal: `results/evolution_proposals/evolved_v5_full_live/proposal.md`
- Candidate genome: `results/evolution_proposals/evolved_v5_full_live/candidate_genome.yaml`

## Next Step

Review the candidate genome manually. If the proposal is accepted, copy or promote it into `configs/`, run `validate-genome`, run a dry-run smoke batch, and only then consider a live evaluation batch.
