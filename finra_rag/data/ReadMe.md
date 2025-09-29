# data/ — runtime artifacts (not checked in)

Structure produced by the pipeline:

- raw_html/YYYY/MM/DD/*.html.gz      # exact HTML snapshots (sha256-named)
- parsed_json/*.json.gz               # per-URL parsed metadata + HTML
- chunks/*.json.gz                    # per-page RAG chunks (arrays)
- exports/jsonl/*.jsonl.gz            # batch export for Vertex AI Search
- manifests/*.json                    # counts, hashes, small run stats

You can safely delete this entire folder to rebuild.
