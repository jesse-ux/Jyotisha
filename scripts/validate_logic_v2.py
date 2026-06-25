#!/usr/bin/env python3
"""
逻辑正确性验证框架 v2
对比 Skill 引擎和 PyJhora 对60张名人星盘的 Yoga 检测结果
"""
import json, sys, os
from pathlib import Path

# ==== 路径 ====
PROJECT_DIR = Path(__file__).resolve().parents[1]
SKILL_DIR = str(PROJECT_DIR)
RULES_PATH = os.path.join(SKILL_DIR, 'references', 'yoga_rules.json')
from yoga_engine import YogaEngine

# CROSS_NAME_MAP: PyJhora Yoga名 → Skill rule_id
# 复用 validate_comprehensive.py 中的映射（简化版，只保留核心映射）
# ---- 从 validate_comprehensive.py 内联的映射逻辑 ----
PYJHORA_VARIANTS = {
    # Dharidhra variants
    'dharidhra_yoga_144': 'bvr_dharidhra_precise',
    'dharidhra_yoga_147': 'bvr_dharidhra_precise',
    'dharidhra_yoga_148': 'bvr_dharidhra_precise',
    'dharidhra_yoga_149': 'bvr_dharidhra_precise',
    'dharidhra_yoga_150': 'bvr_dharidhra_precise',
    'dharidhra_yoga_151': 'bvr_dharidhra_precise',
    'dharidhra_yoga_152': 'bvr_dharidhra_precise',
    # Dehasthoulya variants
    'dehasthoulya_yoga_114': 'bvr_dehasthoulya_yoga',
    'dehasthoulya_yoga_115': 'bvr_dehasthoulya_yoga',
    'dehasthoulya_yoga_116': 'bvr_dehasthoulya_yoga',
    # Mathibhramana variants
    'mathibhramana_yoga_291': 'bvr_mathibhramana_yoga',
    'mathibhramana_yoga_292': 'bvr_mathibhramana_yoga',
    'mathibhramana_yoga_293': 'bvr_mathibhramana_yoga',
    'mathibhramana_yoga_294': 'bvr_mathibhramana_yoga',
    'mathibhramana_yoga_variation': 'bvr_mathibhramana_yoga',
    # Krisanga variants
    'krisanga_yoga_112': 'bvr_krisanga_yoga',
    'krisanga_yoga_113': 'bvr_krisanga_yoga',
    # Kaalanirdesat variants
    'kaalanirdesat_puthra_yoga_227': 'bvr_kaalanirdesat_puthra_yoga',
    'kaalanirdesat_puthra_yoga_228': 'bvr_kaalanirdesat_puthra_yoga',
    'kaalanirdesat_puthranaasa_yoga_230': 'bvr_kaalanirdesat_puthranaasa_yoga',
    # Matrunasa variants
    'matrunasa_yoga_198': 'bvr_matrunasa_precise',
    'matrunasa_yoga_199': 'bvr_matrunasa_precise',
    # Matrudeerghayur variants
    'matrudeerghayur_yoga_196': 'bvr_matrudeerghayur_yoga',
    'matrudeerghayur_yoga_197': 'bvr_matrudeerghayur_yoga',
    # Nishkapata variants
    'nishkapata_yoga_205': 'bvr_nishkapata_precise',
    'nishkapata_yoga_206': 'bvr_nishkapata_precise',
    # Bahu puthra variants
    'bahu_puthra_yoga_220': 'bvr_bahu_puthra_precise',
    'bahu_puthra_yoga_221': 'bvr_bahu_puthra_precise',
    # Bandhu pujya variants
    'bandhu_pujya_yoga_193': 'bvr_bandhu_pujya_yoga',
    'bandhu_pujya_yoga_194': 'bvr_bandhu_pujya_yoga',
    # Ayatna griha prapta variants
    'ayatna_griha_prapta_yoga_189': 'bvr_ayatna_griha_prapta_yoga',
    'ayatna_griha_prapta_yoga_190': 'bvr_ayatna_griha_prapta_yoga',
    # Grihanasa variants
    'grihanasa_yoga_191': 'bvr_grihanasa_yoga',
    'grihanasa_yoga_192': 'bvr_grihanasa_yoga',
    # Dattha puthra variants
    'dattha_puthra_yoga_222': 'bvr_dattha_puthra_yoga',
    'dattha_puthra_yoga_223': 'bvr_dattha_puthra_yoga',
    # Kushtaroga variants
    'kushtaroga_yoga_268': 'bvr_kushtaroga_yoga',
    # Sarpasaapa variants
    'sarpasaapa_yoga_212': 'bvr_sarpasaapa_yoga',
    'sarpasaapa_yoga_213': 'bvr_sarpasaapa_yoga',
    # Raja bhanga variants
    'raja_bhanga_yoga_298': 'bvr_raja_bhanga_yoga',
    'raja_bhanga_yoga_299': 'bvr_raja_bhanga_yoga',
    # Andha variants
    'andha_yoga_288': 'bvr_andha_yoga',
    'andha_yoga_289': 'bvr_andha_yoga',
    # Vahana variants
    'vahana_yoga_209': 'bvr_vahana_yoga',
    'vahana_yoga_210': 'bvr_vahana_yoga',
    # Kapata family
    'kapata_yoga_202': 'bvr_kapata_yoga',
    'kapata_yoga_203': 'bvr_kapata_yoga',
    'kapata_yoga_204': 'bvr_kapata_yoga',
    'pisacha_grastha_yoga': 'bvr_pisacha_grastha_yoga',
    'kaalanirdesat_puthranaasa_yoga_229': 'bvr_kaalanirdesat_puthranaasa_yoga',
    'dwadasa_sahodara_yoga': 'bvr_dwadasa_sahodara_yoga',
    'sapthasankhya_sahodara_yoga': 'bvr_sapthasankhya_sahodara_yoga',
    'karma_malika_yoga': 'bvr_karma_malika_precise',
    'ardha_chandra_yoga': 'bvr_ardha_chandra_yoga',
    # Kalanidhi variants
    'kalaanidhi_yoga': 'bvr_kalaanidhi_yoga',
    'kalanidhi_yoga': 'bvr_kalaanidhi_yoga',
    # Soola/Sula
    'soola_yoga': 'bvr_soola_yoga',
    'sula_yoga': 'bvr_soola_yoga',
    # Kedara
    'kedara_yoga': 'bvr_kedaara_yoga',
    # Kaahala/Kahala are distinct PyJHora functions:
    # - kaahala_yoga: L4 and Jupiter in mutual quadrants + strong L1
    # - kahala_yoga: L4 and L9 in mutual kendras + strong L1
    'kaahala_yoga': 'bvr_kaahala_yoga',
    'kahala_yoga': 'kahala_yoga',
    # Direct mappings for common yogas
    'vosi_yoga': 'bvr_vosi_precise',
    'sunaphaa_yoga': 'bvr_sunaphaa_precise',
    'amala_yoga': 'bvr_amala_precise',
    'anaphaa_yoga': 'bvr_anaphaa_precise',
    'sareera_soukhya_yoga': 'bvr_sareera_soukhya_precise',
    'rogagrastha_yoga': 'bvr_rogagrastha_precise',
    'sada_sanchara_yoga': 'bvr_sada_sanchara_precise',
    'swaveeryaddhana_yoga': 'bvr_swaveeryaddhana_precise',
    'anthya_vayasi_dhana_yoga': 'bvr_anthya_vayasi_dhana_yoga',
    'matrumooladdhana_yoga': 'bvr_matrumooladdhana_yoga',
    'yuddha_praveena_yoga': 'bvr_yuddha_praveena_yoga',
    'bandhubhisthyaktha_yoga': 'bvr_bandhubhisthyaktha_precise',
    'sraddhannabhuktha_yoga': 'bvr_sraddhannabhuktha_precise',
    'bhratruvriddhi_yoga': 'bvr_bhratruvriddhi_precise',
    'sodaranasa_yoga': 'bvr_sodaranasa_yoga',
    'dehapushti_yoga': 'bvr_dehapushti_yoga',
    'mridanga_yoga': 'bvr_mridanga_yoga',
    'bheri_yoga': 'bvr_bheri_yoga',
    'pushkala_yoga': 'bvr_pushkala_yoga',
    'parakrama_yoga': 'bvr_parakrama_yoga',
    'lakshmi_yoga': 'bvr_lakshmi_yoga',
    'adhi_yoga': 'bvr_adhi_yoga',
    'brahma_yoga': 'bvr_brahma_yoga',
    'bhandhana_yoga': 'bvr_bhandhana_yoga',
    'harihara_brahma_yoga': 'bvr_harihara_brahma_yoga',
    'hara_yoga': 'bvr_hara_yoga',
    'hari_yoga': 'bvr_hari_yoga',
    'madhya_vayasi_dhana_yoga': 'bvr_madhya_vayasi_dhana_yoga',
    'balya_dhana_yoga': 'bvr_balya_dhana_yoga',
    'go_yoga': 'bvr_go_yoga',
    'sara_yoga': 'bvr_sara_yoga',
    'ishu_yoga': 'bvr_ishu_yoga',
    'kshayaroga_yoga': 'bvr_kshayaroga_yoga',
    'kalatramooladdhana_yoga': 'bvr_kalatramooladdhana_yoga',
    'vishnu_yoga': 'bvr_vishnu_yoga',
    'vichitra_saudha_prakara_yoga': 'bvr_vichitra_saudha_prakara_yoga',
    'jananatpurvam_pitru_marana_yoga': 'bvr_jananatpurvam_pitru_marana_yoga',
    'bhratrumooladdhanaprapti_yoga': 'bvr_bhratrumooladdhanaprapti_yoga',
    'thrikaala_gnana_yoga': 'bvr_thrikaala_gnana_yoga',
    'yuddhatpaschaddrudha_yoga': 'bvr_yuddhatpaschaddrudha_yoga',
    'yuddhatpoorvadridhachitta_yoga': 'bvr_yuddhatpoorvadridhachitta_yoga',
    'dhurmarana_yoga': 'bvr_dhurmarana_yoga',
    'theevrabuddhi_yoga': 'bvr_theevrabuddhi_yoga',
    'vaatharoga_yoga': 'bvr_vaatharoga_yoga',
    'amaranantha_dhana_yoga': 'bvr_amaranantha_dhana_yoga',
    'pittharoga_yoga': 'bvr_pittharoga_yoga',
    'sarpasaapa_yoga': 'bvr_sarpasaapa_yoga',
    'parannabhojana_yoga': 'bvr_parannabhojana_yoga',
    'veenaa_yoga': 'bvr_veenaa_yoga',
    'duradhara_yoga': 'bvr_duradhara_yoga',
    'annadana_yoga': 'bvr_annadana_yoga',
    'yukthi_samanwithavagmi_yoga_154': 'bvr_yukthi_samanwithavagmi_yoga',
    'nipuna_yoga': 'bvr_nipuna_yoga',
    'surya_budha_yoga': 'bvr_nipuna_yoga',
    'parvata_yoga': 'bvr_parvata_yoga',
    'hamsa_yoga': 'bvr_hamsa_yoga',
    'ruchaka_yoga': 'bvr_ruchaka_yoga',
    'bhadra_yoga': 'bvr_bhadra_yoga',
    'chatussagara_yoga': 'bvr_chatussagara_yoga',
    'sarpa_yoga': 'bvr_sarpa_yoga',
    'kemadruma_yoga': 'bvr_kemadruma_yoga',
    'sankha_yoga': 'bvr_sankha_yoga',
    'sumukha_yoga': 'bvr_sumukha_yoga',
    'ubhayachara_yoga': 'bvr_ubhayachara_yoga',
    'sasa_yoga': 'bvr_sasa_yoga',
    'matsya_yoga': 'bvr_matsya_yoga',
    'koorma_yoga': 'bvr_koorma_yoga',
    'naukaa_yoga': 'bvr_naukaa_yoga',
    'vihaga_yoga': 'bvr_vihaga_yoga',
    'yuga_yoga': 'bvr_yuga_yoga',
    'gola_yoga': 'bvr_gola_yoga',
    # Fix previously unmapped
    'matru_sneha_yoga': 'bvr_matru_sneha_yoga',
    'eka_puthra_yoga': 'bvr_eka_puthra_precise',
    'guru_mangala_yoga': 'bvr_103_guru_mangala_yoga',
    'vanchana_chora_bheethi_yoga': 'bvr_vanchana_chora_bheethi_yoga',
    'bahu_sthree_yoga': 'bvr_bahu_sthree_yoga',
    'dama_yoga': 'bvr_dama_yoga',
    'utthama_graha_yoga': 'bvr_utthama_graha_yoga',
    'chandra_mangala_yoga': 'bvr_105_chandra_mangala_yoga',
    'bhaga_chumbana_yoga': 'bvr_bhaga_chumbana_yoga',
    'yuddha_marana_yoga': 'bvr_yuddha_marana_yoga',
    'andha_yoga': 'bvr_andha_yoga',
    'matru_satrutwa_yoga': 'bvr_matru_satrutwa_yoga',
    'apakeerthi_yoga': 'bvr_apakeerthi_yoga',
}


RULE_ID_ALIASES = {
    # Historical/numbered rule ids in yoga_rules.json
    'bvr_vosi_precise': 'bvr_017_vosi_precise',
    'bvr_sunaphaa_precise': 'bvr_002_sunapha_precise',
    'bvr_anaphaa_precise': 'bvr_003_anapha_precise',
    'bvr_duradhara_yoga': 'bvr_004_duradhara_precise',
    'bvr_ubhayachara_yoga': 'bvr_018_ubhayachara_precise',
    'bvr_dharidhra_precise': 'bvr_dharidhra_11_precise',
    'bvr_sara_yoga': 'bvr_072_sara',
    'bvr_ishu_yoga': 'bvr_072_ishu',
    'bvr_naukaa_yoga': 'bvr_075_naukaa_precise',
    'bvr_vihaga_yoga': 'vihaga_nabhasa',
    'bvr_veenaa_yoga': 'veena_yoga',
    'bvr_sumukha_yoga': 'bvr_sumukha_precise',
}


def canonical_rule_id(rule_id, valid_rule_ids):
    """Map historical validation ids to actual enabled yoga_rules.json ids."""
    if not rule_id:
        return None
    if rule_id in valid_rule_ids:
        return rule_id
    alias = RULE_ID_ALIASES.get(rule_id)
    if alias in valid_rule_ids:
        return alias
    if rule_id.startswith('bvr_'):
        without_bvr = rule_id[4:]
        candidates = [without_bvr]
        if without_bvr.endswith('_precise'):
            base = without_bvr[:-8]
            candidates.extend([base, f'{base}_yoga'])
        for candidate in candidates:
            if candidate in valid_rule_ids:
                return candidate
    return None


def extract_skill_rule_ids(skill_results):
    """Extract comparable rule ids while ignoring algorithmic Yoga rows."""
    ids = set()
    for row in skill_results:
        if not isinstance(row, dict):
            continue
        rule_id = row.get('rule_id') or row.get('id')
        if isinstance(rule_id, str) and rule_id:
            ids.add(rule_id)
    return ids

# ---- 内联结束 ----


def main():
    # 1. 加载位置数据。固定使用 skill 内部 references，避免从其他 cwd 运行时读写错目录。
    planet_positions_path = os.path.join(SKILL_DIR, 'references', 'planet_positions_60.json')
    standard_charts_path = os.path.join(SKILL_DIR, 'references', 'standard_test_charts.json')
    report_path = os.path.join(SKILL_DIR, 'references', 'validation_logic_report.json')
    with open(planet_positions_path) as f:
        pos_data = json.load(f)

    # 2. 加载 PyJhora Yoga 结果
    with open(standard_charts_path) as f:
        pyj_data = json.load(f)

    # 构建 name -> pyjhora yoga list 映射
    pyj_charts = {c['name']: c for c in pyj_data['charts']}

    # 3. 加载 Skill 引擎
    engine = YogaEngine(RULES_PATH)

    # 构建 rule_id -> rule_name 映射
    rule_id_to_name = {r['id']: r['name'] for r in engine.rules}
    # 以及 name -> rule_id 反向映射（用于去重匹配）
    name_to_rule_ids = {}
    for r in engine.rules:
        name = r['name']
        name_to_rule_ids.setdefault(name, []).append(r['id'])

    valid_rule_ids = set(rule_id_to_name.keys())
    # 建立"可对比规则集"：仅保留真实存在且启用的 Skill rule_id，避免历史 ID 别名造成 60/60 假性 FN。
    variant_to_rule_id = {}
    missing_mappings = {}
    for py_name, raw_id in PYJHORA_VARIANTS.items():
        canonical = canonical_rule_id(raw_id, valid_rule_ids)
        if canonical:
            variant_to_rule_id[py_name] = canonical
        else:
            missing_mappings.setdefault(raw_id, []).append(py_name)
    comparable_rule_ids = set(variant_to_rule_id.values())
    print(f"可对比规则数量: {len(comparable_rule_ids)}")
    if missing_mappings:
        print(f"暂不可对比映射数量: {len(missing_mappings)}")

    # 统计（只统计可对比规则）
    total_skill_comp = 0   # Skill在可对比规则集中的检测数
    total_pyj_comp = 0     # PyJhora能映射到可对比规则的检测数
    total_agreements = 0
    total_false_positives = 0
    total_false_negatives = 0
    total_unmapped_pyj = 0

    fp_details = []   # Skill说有，PyJhora说没有（都在可对比集内）
    fn_details = []   # PyJhora说有，Skill说没有（都在可对比集内）

    for chart in pos_data['charts']:
        name = chart['name']
        planets = chart['planets']
        ascendant = chart['ascendant']

        # 从 standard_test_charts.json 取完整 context（含 D9/Navamsa/Upagraha 数据）
        pyj_chart = pyj_charts.get(name)
        if not pyj_chart:
            print(f"  WARNING: {name} not in PyJhora data")
            continue
        context = pyj_chart.get('context', {})
        # Skill 引擎检测（使用含 D9 的完整 context）
        skill_results = engine.detect(planets, ascendant, context=context)
        skill_yoga_ids = extract_skill_rule_ids(skill_results)
        skill_comp = skill_yoga_ids & comparable_rule_ids  # 只保留可对比的
        total_skill_comp += len(skill_comp)

        pyj_yoga_names = set(pyj_chart.get('expected_yogas', []))

        # 将 PyJhora Yoga名映射到 Skill rule_id
        pyj_mapped_ids = set()
        unmapped = 0
        for pyj_name in pyj_yoga_names:
            mapped = variant_to_rule_id.get(pyj_name)
            if not mapped:
                norm = pyj_name.lower().strip()
                mapped = variant_to_rule_id.get(norm)
            if mapped:
                pyj_mapped_ids.add(mapped)
            else:
                unmapped += 1
        total_unmapped_pyj += unmapped
        pyj_comp = pyj_mapped_ids & comparable_rule_ids
        total_pyj_comp += len(pyj_comp)

        # 对比（只对比可对比规则集）
        agreements = skill_comp & pyj_comp
        false_positives = skill_comp - pyj_comp  # Skill说有，PyJhora说没有
        false_negatives = pyj_comp - skill_comp  # PyJhora说有，Skill说没有

        total_agreements += len(agreements)
        total_false_positives += len(false_positives)
        total_false_negatives += len(false_negatives)

        if false_positives:
            for rid in sorted(false_positives):
                fp_details.append({
                    'chart': name,
                    'rule_id': rid,
                    'rule_name': rule_id_to_name.get(rid, '?'),
                })
        if false_negatives:
            for rid in sorted(false_negatives):
                orig_names = sorted(pn for pn, sid in variant_to_rule_id.items() if sid == rid)
                fn_details.append({
                    'chart': name,
                    'rule_id': rid,
                    'rule_name': rule_id_to_name.get(rid, '?'),
                    'pyjhora_names': orig_names,
                })

    # ==== 输出报告 ====
    print("=" * 70)
    print("Skill vs PyJhora 逻辑正确性验证报告（仅可对比规则）")
    print("=" * 70)
    print(f"测试星盘数量: 60")
    print(f"可对比规则集大小: {len(comparable_rule_ids)}")
    print(f"PyJhora未映射Yoga: {total_unmapped_pyj}")
    print()
    print(f"Skill 可对比检测总数: {total_skill_comp}")
    print(f"PyJhora 可对比检测总数: {total_pyj_comp}")
    print(f"一致 (Agreements): {total_agreements}")
    print(f"False Positives (Skill过宽): {total_false_positives}")
    print(f"False Negatives (Skill过严): {total_false_negatives}")
    print()

    precision = total_agreements / total_skill_comp if total_skill_comp else 0
    recall = total_agreements / total_pyj_comp if total_pyj_comp else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0

    print(f"Precision (准确率): {precision:.2%}")
    print(f"Recall (召回率):    {recall:.2%}")
    print(f"F1 Score:           {f1:.2%}")
    print()

    # 按规则汇总 FP
    if fp_details:
        from collections import Counter
        fp_by_rule = Counter((d['rule_id'], d['rule_name']) for d in fp_details)
        print("--- False Positives 最多的规则 (Top 20) ---")
        for (rid, rname), count in fp_by_rule.most_common(20):
            print(f"  {count:2d} 次: {rid} ({rname})")
        print()

    # 按规则汇总 FN
    if fn_details:
        from collections import Counter
        fn_by_rule = Counter((d['rule_id'], d['rule_name']) for d in fn_details)
        print("--- False Negatives 最多的规则 (Top 20) ---")
        for (rid, rname), count in fn_by_rule.most_common(20):
            print(f"  {count:2d} 次: {rid} ({rname})")
        print()

    # 保存详细报告
    report = {
        "summary": {
            "charts_tested": 60,
            "comparable_rules": len(comparable_rule_ids),
            "skill_total": total_skill_comp,
            "pyjhora_total": total_pyj_comp,
            "unmapped_pyjhora": total_unmapped_pyj,
            "missing_mappings": {k: v for k, v in sorted(missing_mappings.items())},
            "agreements": total_agreements,
            "false_positives": total_false_positives,
            "false_negatives": total_false_negatives,
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4),
        },
        "false_positives": sorted(fp_details, key=lambda row: (row["chart"], row["rule_id"])),
        "false_negatives": sorted(fn_details, key=lambda row: (row["chart"], row["rule_id"])),
    }
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"详细报告已保存至: {report_path}")


if __name__ == "__main__":
    main()
