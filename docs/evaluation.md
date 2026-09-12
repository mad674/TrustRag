# Evaluation Framework

## Goal

The evaluation framework must compare retrieval quality, generation faithfulness, and trustworthiness using actual experimental outputs rather than hard-coded claims.

## Base metrics

### Retrieval metrics

- Precision@K
- Recall@K
- MRR
- nDCG@K

### Generation metrics

- faithfulness
- answer relevancy
- context precision
- context recall

### Trust metrics

- hallucination rate
- citation completeness
- evidence coverage
- verification accuracy

### Performance metrics

- response latency
- retrieval latency
- reranking latency
- token usage when available
- estimated cost when available

## Ablation study

The framework should evaluate:

- full system
- no adaptive retrieval
- no reranking
- no verification
- no multi-agent layer
- no explainability

## Output products

The benchmark runner should generate:

- CSV output
- JSON output
- plots
- comparison table
- per-run metadata

## Important rule

The project does not present any numerical results unless they are produced by the actual evaluation pipeline.
