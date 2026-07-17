from pathlib import Path
from scripts.xalen_ephemeris_mode_comparison import compare
ROOT=Path(__file__).resolve().parents[1]
def test_independent_xalen_ephemeris_is_separately_disclosed() -> None:
 r=compare(ROOT/'references/oracle/artifacts/xalen_steve_jobs_high_rigor_raw.json',ROOT/'references/oracle/artifacts/xalen_steve_jobs_independent_ephemeris_raw.json')
 assert r['shared_mode']=='shared_input'
 assert r['independent_mode']=='independent_ephemeris'
 assert r['maximum_absolute_longitude_delta_deg']<0.02
 assert r['varga_difference_count']==0
 assert 'house numbers remain shared' in r['boundary']
