# Tajika Einstein 1905 Packet Paste Instructions

原 packet:
`references/oracle/artifacts/pending_packets/external_template_einstein_varshaphala_1905_lahiri.json`

可直接粘贴块:
`docs/benchmark/tajika_einstein_1905_packet_paste_block.jsonc`

## 最省力用法

不要从头编辑整个 packet。

直接做这 4 步:

1. 打开原 packet  
2. 找到并替换这 3 段:
   - 顶层 `status`
   - `metadata`
   - `target_placeholders`
3. 把 `tajika_einstein_1905_packet_paste_block.jsonc` 里的对应内容整段复制进去
4. 只替换 `<...>` 占位符

## 你真正需要改的只有这些占位符

- `<version>`
- `<artifact-file>`
- `<tool/source>`
- `<fill>`
- `<copy exact timestamp with offset>`
- `<absolute zodiac degree>`
- `<sign name>`
- `<planet name>`
- `<copy exact yoga labels from external source>`

## 注意

- `jsonc` 文件只是为了让人更方便复制, 占位符替换完后, 最终落回原 packet 时必须保持合法 JSON
- `target.source_artifact` 与 `metadata.source_artifact` 要一致
- `target.tajika_yogas` 优先照外部工具原样抄, 不要翻译成本地解释术语
- 如果外部工具不是 `PyJHora`, 只改 `tool_name` 和 `tool_version_or_url`, 其他结构照抄即可

## 填完立刻执行

```bash
python3 scripts/tajika_annual_oracle_queue.py \
  --oracle-file references/oracle/tajika_annual_oracle_cases.json \
  --apply-packet references/oracle/artifacts/pending_packets/external_template_einstein_varshaphala_1905_lahiri.json \
  --format json
```

```bash
python3 scripts/tajika_annual_benchmark_dashboard.py \
  --oracle-file references/oracle/tajika_annual_oracle_cases.json \
  --format json
```
