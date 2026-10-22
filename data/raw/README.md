# data/raw - raw data (add-only)
- File name: `<first 16 hex of sha256>__<original name>`
- Every file is registered in `MANIFEST.yaml` with source, fetch date and licence.
- If a renamed file has an original name, record it in `original_name`.
- Gate `check_raw_immutable.py` rejects any modification or deletion.
- Raw files that conflict with the language rule are listed in `audit/EXCEPTIONS.yaml`, never edited.
