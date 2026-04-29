/**
 * Argala（门闩）行星干预模块 v1.0
 * 移植自 Python argala.py
 *
 * Parashara体系的行星影响力锁定机制:
 *   - 主Argala: 2/4/11宫位产生正面干预
 *   - 副Argala: 5/8宫位产生正面干预
 *   - Virodha Argala: 12/10/3/9/2宫位产生反向阻止
 */

const BENEFICS = new Set(['Jupiter', 'Venus', 'Moon']);
const MALEFICS = new Set(['Saturn', 'Mars', 'Sun', 'Rahu', 'Ketu']);

const MAIN_ARGALA = [2, 4, 11];
const SUB_ARGALA = [5, 8];
const VIRODHA = { 2: 12, 4: 10, 11: 3, 5: 9, 8: 2 };

const ARGALA_EFFECTS = {
  2: { benefic: '财富和资源流入', malefic: '财务压力和资源消耗' },
  4: { benefic: '幸福感、住所和内心平静增强', malefic: '家庭不和、住所问题' },
  11: { benefic: '收益、愿望实现和社会认可', malefic: '损失、社会障碍' },
  5: { benefic: '智慧、权力和创造力增强', malefic: '智力困扰、决策失误' },
  8: { benefic: '隐藏资源和转化力量', malefic: '隐藏障碍和突发危机' },
};

function argalaEffect(house, nature) {
  return ARGALA_EFFECTS[house]?.[nature] || '一般性影响';
}

function isBenefic(p) { return BENEFICS.has(p); }

/**
 * 计算所有行星的 Argala 和 Virodha Argala
 * @param {Object} planetSignIdx - { Sun: 0, Moon: 3, ... } 行星所在星座索引
 * @param {number} ascSignIdx - 上升星座索引
 * @returns {Object} 每颗行星的 argala 分析结果
 */
export function computeArgala(planetSignIdx, ascSignIdx) {
  // 计算各行星宫位
  const houses = {};
  for (const [pn, si] of Object.entries(planetSignIdx)) {
    houses[pn] = ((si - ascSignIdx) % 12 + 12) % 12 + 1;
  }

  const results = {};
  const planetNames = Object.keys(houses);

  for (const targetP of planetNames) {
    const targetH = houses[targetP];
    const argalaOnTarget = [];
    const virodhaOnTarget = [];
    const argalaByTarget = [];

    for (const sourceP of planetNames) {
      if (sourceP === targetP) continue;
      const sourceH = houses[sourceP];
      const rel = ((sourceH - targetH) % 12 + 12) % 12 + 1;

      // 主Argala检查
      if (MAIN_ARGALA.includes(rel)) {
        const nature = isBenefic(sourceP) ? 'benefic' : 'malefic';
        argalaOnTarget.push({
          source: sourceP, house_from: rel,
          type: 'main', nature, strength: 'normal',
          effect: argalaEffect(rel, nature),
        });
      }
      // 副Argala检查
      else if (SUB_ARGALA.includes(rel)) {
        const nature = isBenefic(sourceP) ? 'benefic' : 'malefic';
        argalaOnTarget.push({
          source: sourceP, house_from: rel,
          type: 'sub', nature, strength: 'conditional',
          effect: argalaEffect(rel, nature),
        });
      }

      // Virodha检查
      for (const [aHouse, vHouse] of Object.entries(VIRODHA)) {
        if (rel === vHouse) {
          const nature = isBenefic(sourceP) ? 'benefic' : 'malefic';
          virodhaOnTarget.push({
            source: sourceP, house_from: rel,
            blocks_argala_from: parseInt(aHouse),
            nature,
          });
        }
      }
    }

    // 此行星对其他位置产生的Argala
    for (const relHouse of MAIN_ARGALA) {
      const targetHouse = ((targetH - 1 + relHouse - 1) % 12) + 1;
      const planetsThere = planetNames.filter(p => houses[p] === targetHouse);
      if (planetsThere.length > 0) {
        const nature = isBenefic(targetP) ? 'benefic' : 'malefic';
        argalaByTarget.push({
          argala_type: `${relHouse}宫Argala`,
          target_house: targetHouse,
          affects: planetsThere,
          effect: argalaEffect(relHouse, nature),
        });
      }
    }

    // 净Argala评估
    const beneficA = argalaOnTarget.filter(a => a.nature === 'benefic').length;
    const maleficA = argalaOnTarget.filter(a => a.nature === 'malefic').length;
    const beneficV = virodhaOnTarget.filter(v => v.nature === 'benefic').length;
    const maleficV = virodhaOnTarget.filter(v => v.nature === 'malefic').length;
    const net = (beneficA - maleficV) - (maleficA - beneficV);

    results[targetP] = {
      house: targetH,
      argala_on_this: argalaOnTarget,
      virodha_on_this: virodhaOnTarget,
      argala_by_this: argalaByTarget,
      net_score: net,
      net_assessment: net >= 2 ? 'strongly_supported' : net >= 1 ? 'supported'
        : net <= -2 ? 'blocked' : 'neutral',
    };
  }

  return results;
}
