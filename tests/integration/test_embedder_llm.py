def test_embedder_records_retrievable_by_llm(llm_embedder_env):
    env = llm_embedder_env
    env["ingest"](
        [
            {
                "id": "doc-1",
                "text": "Stock markets rallied strongly today.",
                "title": "Market Update",
                "source_url": "http://example.com/article",
            }
        ]
    )

    context, citations = env["llm_service"].retrieve_context("market outlook", top_k=1, method="cosine")
    assert "Stock markets rallied strongly today." in context
    assert citations
    assert citations[0]["label"] == "Market Update"
