# Minute Rectification P0 Plan

1. Add failing tests for canonical input hashes, candidate fingerprints and
   pending stability probes.
2. Add a small shared input-contract helper and wire it into the sensitivity
   scanner and private three-engine receipt.
3. Correct public-case coordinate defaults and test them.
4. Add a semantic evidence-hash helper without replacing raw artifact hashes.
5. Run focused tests and inspect the resulting JSON contracts.
