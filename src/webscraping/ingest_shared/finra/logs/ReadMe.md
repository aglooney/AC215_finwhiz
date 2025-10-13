# logs/
- crawl.log    : HTTP fetch + enqueue stats per run
- pipeline.log : transform/export summaries

Log rotation is handled in code (RotatingFileHandler).