# External Oracle Capture Next Steps

First priority packet:

`external_template_steve_jobs_dasha_lahiri.json`

## Fill The Packet

1. Open JHora, PyJHora, VedAstro, or another documented external source.
2. Use the exact birth data, ayanamsa, node mode, timezone, and settings in the packet.
3. Save a redacted screenshot or stdout snippet under `references/oracle/artifacts/`.
4. Fill all metadata fields and all `target_placeholders`.
5. Set `status` to `external_verified` only after the artifact and target values are filled.

不得把本仓库本地输出当作 external oracle。

## Apply The Packet

```bash
python3 scripts/oracle_collection_queue.py \
  --oracle-file references/oracle/dasha_shadbala_oracle_cases.json \
  --apply-packet /Users/wuyongnaren/Documents/印度占星/references/oracle/artifacts/pending_packets/external_template_steve_jobs_dasha_lahiri.json \
  --format json
```

## Validate Again

```bash
python3 scripts/oracle_collection_queue.py \
  --oracle-file references/oracle/dasha_shadbala_oracle_cases.json \
  --format json > /tmp/jyotish_oracle_queue_filled.json

python3 scripts/oracle_evidence_validator.py \
  --queue-file /tmp/jyotish_oracle_queue_filled.json
```

Draft packets in `references/oracle/artifacts/pending_packets` must remain `valid_packets: 0` until real external evidence is filled.
