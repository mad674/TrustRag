# TrustRAG Research Implementation

## Phase Endpoints

- Baseline Dense RAG: `POST /api/retrieve/baseline`
- Adaptive RAG: `POST /api/adaptive/rag`
- Multi-agent TrustRAG: `POST /api/orchestrate/query`
- Phase Comparison: `POST /api/evaluation/compare`

## Novelty 1: Adaptive Retrieval Selection

TrustRAG does not use hybrid retrieval for every query. It classifies intent first, then selects the retrieval strategy:

| Intent | Strategy |
| --- | --- |
| Definition | BM25 |
| Comparison | Hybrid |
| Summarization | Dense |
| Research Gap | Hybrid + Reranker |
| Citation | Dense |
| Question Answering | Hybrid |

### Pseudocode

```text
function adaptive_retrieve(query, top_k):
    intent = classify_query(query)
    strategy = strategy_table[intent]

    if strategy == BM25:
        candidates = bm25(query)
    else if strategy == Dense:
        candidates = dense_vector_search(query)
    else:
        candidates = merge(bm25(query), dense_vector_search(query))

    if strategy == Hybrid + Reranker:
        candidates = rerank(query, candidates)

    return top_k(candidates)
```

## Novelty 2: Evidence Verification

TrustRAG verifies the generated answer against retrieved evidence before returning it.

```text
contexts = adaptive_retrieve(query)
answer = generate_answer(query, contexts)
verification = compare_answer_to_context(answer, contexts)
confidence = weighted_score(evidence_match, similarity)
return answer, confidence, hallucination_score, supporting_chunks
```

## Novelty 3: Confidence Explainability

Every response includes:

- Confidence score
- Evidence score
- Hallucination score and risk
- Supporting chunks
- Source titles and chunk indexes
- Similarity/relevance scores
- Retrieval intent and selected strategy

## Evaluation Design

Use `/api/evaluation/compare` to compare:

1. Dense baseline RAG
2. Fixed hybrid RAG
3. Fixed hybrid + reranker
4. TrustRAG adaptive retrieval

Metrics returned by the implementation:

- Precision@K, if relevant document IDs are provided
- Recall@K, if relevant document IDs are provided
- Evidence score
- Hallucination score
- Confidence
- Latency
- Retrieval strategy and reranker use
