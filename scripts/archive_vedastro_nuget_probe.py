#!/usr/bin/env python3
"""Merge pinned NuGet metadata with the container runtime reflection probe."""

from __future__ import annotations

import argparse, json
from pathlib import Path

def build_archive(candidate: Path, runtime: Path) -> dict:
    metadata=json.loads(candidate.read_text(encoding="utf-8")); probe=json.loads(runtime.read_text(encoding="utf-8"))
    return {**metadata,"assembly_version":probe["version"],"assembly_informational_version":probe["informational_version"],"public_methods":probe["methods"],"public_method_contracts":probe["method_contracts"],"runtime_image_id":"sha256:ea4f5eec20952a885a89566fc35cf3295b3228375b715a0f1af9e5a3c0c2eebf","runtime_image_digest":"sha256:d32bd65cf5843f413e81f5d917057c82da99737cb1637e905a1a4bc2e7ec6c8d"}

def main()->int:
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("runtime",type=Path);p.add_argument("--candidate",type=Path,default=Path("references/oracle/vedastro_nuget_candidate_1_2_0.json"));p.add_argument("--output",type=Path,required=True);a=p.parse_args();r=build_archive(a.candidate,a.runtime);a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(r,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8");print(json.dumps({"status":r["status"],"method_count":len(r["public_methods"])},sort_keys=True));return 0
if __name__=="__main__":raise SystemExit(main())
