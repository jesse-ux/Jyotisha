#!/usr/bin/env python3
"""Attribute Xalen Shadbala and Ashtakavarga differences by formula and unit."""

from __future__ import annotations
import argparse,json
from collections import Counter
from pathlib import Path

FORMULAS={
"sthana":("precise sapta-varga dignity with compound temporary relationships and moolatrikona","Xalen sapta-varga dignity using fixed unit friendship scores","formula_variant","Virupa"),
"dig":("longitude distance from exact powerless bhava midpoint / 3","house-number distance from strongest house, linearly scaled","geometry_variant","Virupa"),
"kala":("actual local sunrise/sunset, declination and ahargana Varsha/Maasa/Vaara/Hora","clock day_fraction with nominal 06:00 sunrise plus JD-derived lords","solar_context_variant","Virupa"),
"chesta":("bounded BPHS/Surya mean-motion Seeghrochcha implementation","speed bands: retrograde=60, stationary=30, direct=15; Sun/Moon=30","motion_model_variant","Virupa"),
"drik":("continuous Sphuta Drishti curve, natural benefic/malefic, divided by 4","house-bin graded Vedic aspects, natural benefic/malefic, divided by 4","aspect_interpolation_variant","Virupa"),
}

def build_report(path:Path)->dict:
 d=json.loads(path.read_text(encoding="utf-8")); rows=[]; counts=Counter()
 for r in d["rows"]:
  if r["status"]!="mismatch" or r["section"] not in {"shadbala_components","shadbala_total","ashtakavarga_bav","ashtakavarga_sav"}:continue
  item={"section":r["section"],"field":r["field"],"local_value":r["local_value"],"xalen_value":r["xalen_value"]}
  if r["section"]=="shadbala_components":
   component=r["field"].split(".",1)[1]; local,xalen,category,unit=FORMULAS[component];item.update(category=category,unit=unit,local_formula=local,xalen_formula=xalen,truth_status="method_variant_unresolved")
  elif r["section"]=="shadbala_total": item.update(category="derived_total_from_five_component_variants",unit="Virupa",local_formula="sum of six displayed components",xalen_formula="sum of six displayed components",truth_status="defer_until_components_arbitrated")
  else:
   lv,xv=r["local_value"],r["xalen_value"]; delta=[b-a for a,b in zip(lv,xv)];item.update(category="contributor_table_variant",unit="bindu_count",delta_by_sign=delta,local_formula="PVR/PyJHora worked-example calibrated 8-contributor BAV tables; SAV excludes Lagna row",xalen_formula="Xalen BPHS-labelled 8-contributor tables; returned SAV sums seven planetary rows",row_total_local=sum(lv),row_total_xalen=sum(xv),truth_status="requires_external_worked_example_per_contributor")
  counts[item["category"]]+=1;rows.append(item)
 return {"scope":"xalen_formula_unit_attribution","row_count":len(rows),"classified_count":sum(counts.values()),"category_counts":dict(sorted(counts.items())),"rows":rows,"status":"classified_method_variants_not_truth"}

def main()->int:
 p=argparse.ArgumentParser(description=__doc__);p.add_argument("comparison",type=Path,nargs="?",default=Path("references/oracle/xalen_fourth_oracle_comparison_2026_07_17.json"));p.add_argument("--output",type=Path);a=p.parse_args();r=build_report(a.comparison);text=json.dumps(r,ensure_ascii=False,indent=2,sort_keys=True)+"\n";
 if a.output:a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(text,encoding="utf-8")
 print(text,end="");return 0
if __name__=="__main__":raise SystemExit(main())
