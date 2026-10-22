# src - analysis code
Scripts read `data/raw` or `data/derived` and write `data/derived` or `research/experiment/E-xxx/runs/R-xxxx/`.
Every script that produces a formal output is a step in `pipeline.yaml`. Locate files from the project root (`Path(__file__).resolve().parents[N]`), never absolute paths.
