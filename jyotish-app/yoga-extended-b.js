/**
 * Jyotish 扩展 Yoga 定义库 (Part 2)
 * 宫位关联 Yogas + 特殊 Yogas
 */
const signs = ['Aries','Taurus','Gemini','Cancer','Leo','Virgo','Libra','Scorpio','Sagittarius','Capricorn','Aquarius','Pisces'];
const signIdx = s => signs.indexOf(s);
const lordOf = {Aries:'Mars',Taurus:'Venus',Gemini:'Mercury',Cancer:'Moon',Leo:'Sun',Virgo:'Mercury',Libra:'Venus',Scorpio:'Mars',Sagittarius:'Jupiter',Capricorn:'Saturn',Aquarius:'Saturn',Pisces:'Jupiter'};
const lordOfHouse = (asc, h) => lordOf[signs[(signIdx(asc) + h - 1) % 12]];
const allPlanets = ['Sun','Moon','Mars','Mercury','Jupiter','Venus','Saturn'];

export const YOGA_EXTENDED_B = [
  // House-based Yogas
  {id:'laxmi_narayana',name:'Lakshmi-Narayana Yoga',name_cn:'吉祥神格局',category:'House',check:(p,asc)=>{const l1=lordOfHouse(asc,1),l9=lordOfHouse(asc,9);if(l1===l9)return null;if(p[l1]&&p[l9]&&p[l1].house===p[l9].house&&[1,4,7,10].includes(p[l1].house))return`1宫主${l1}+9宫主${l9}同宫于角宫`;return null},effects:'极度幸运、灵性+物质双丰收',strength:'极强'},
  {id:'dhan_yoga',name:'Dhana Yoga',name_cn:'财富格局',category:'House',check:(p,asc)=>{const wl=[lordOfHouse(asc,2),lordOfHouse(asc,11)];const tl=[lordOfHouse(asc,1),lordOfHouse(asc,5),lordOfHouse(asc,9)];for(const w of wl){for(const t of tl){if(w!==t&&p[w]&&p[t]&&p[w].house===p[t].house)return`财宫主${w}+三角宫主${t}同宫`}}return null},effects:'财富积累、投资运、商业成功',strength:'强'},
  {id:'sama_raja',name:'Sama Raja Yoga',name_cn:'平等帝王格局',category:'House',check:(p,asc)=>{const l7=lordOfHouse(asc,7),l10=lordOfHouse(asc,10);if(l7===l10)return null;if(p[l7]&&p[l10]&&p[l7].house===p[l10].house)return`7宫主${l7}+10宫主${l10}同宫`;return null},effects:'合伙+事业结合、商业合作带来事业巅峰',strength:'强'},
  {id:'vasumati',name:'Vasumati Yoga',name_cn:'大地女神格局',category:'House',check:(p)=>{const b=['Jupiter','Venus','Mercury'];const c=b.filter(n=>p[n]&&[3,6,10,11].includes(p[n].house)).length;return c>=2?`${c}颗吉星在上升宫(3/6/10/11)`:null},effects:'财富不断增长',strength:'中强'},
  {id:'sankha',name:'Sankha Yoga',name_cn:'海螺格局',category:'House',check:(p,asc)=>{const l5=lordOfHouse(asc,5),l6=lordOfHouse(asc,6);if(l5===l6)return null;if(p[l5]&&p[l6]&&p[l5].house===p[l6].house)return`5宫主${l5}+6宫主${l6}同宫`;return null},effects:'战胜敌人后获得快乐',strength:'中强'},
  {id:'bheri',name:'Bheri Yoga',name_cn:'鼓声格局',category:'House',check:(p,asc)=>{const l2=lordOfHouse(asc,2),l10=lordOfHouse(asc,10);if(l2===l10)return null;if(p[l2]&&p[l10]&&p[l2].house===p[l10].house&&[1,4,7,10].includes(p[l2].house))return`2宫主${l2}+10宫主${l10}同宫于角宫`;return null},effects:'名声远播、旅行运、丰富人生',strength:'中强'},
  {id:'mridu',name:'Mridu Yoga',name_cn:'温和格局',category:'House',check:(p)=>{const b=['Jupiter','Venus','Mercury','Moon'];const c=b.filter(n=>p[n]&&[1,4,7,10].includes(p[n].house)).length;return c>=3?`${c}颗吉星在角宫`:null},effects:'温和成功、受人爱戴',strength:'中强'},
  {id:'kurma',name:'Kurma Yoga',name_cn:'龟神格局',category:'House',check:(p,asc)=>{const l3=lordOfHouse(asc,3),l4=lordOfHouse(asc,4);if(l3===l4)return null;if(p[l3]&&p[l4]&&[1,4,7,10].includes(p[l3].house)&&[1,4,7,10].includes(p[l4].house))return`3宫主+4宫主均在角宫`;return null},effects:'勇气+家庭幸福并存',strength:'中强'},

  // Special Yogas
  {id:'maha_bhagya',name:'Maha Bhagya Yoga',name_cn:'大好运格局',category:'Special',check:(p,asc)=>{const ai=signIdx(asc);const isDayAsc=[0,4,5,8,9].includes(ai);const sunDay=p.Sun&&[1,4,7,10].includes(p.Sun.house);const moonDay=p.Moon&&[1,4,7,10].includes(p.Moon.house);if(isDayAsc&&sunDay&&moonDay)return'日生盘+日月在角宫';const isNightAsc=[1,2,3,6,7,10,11].includes(ai);const sunNight=p.Sun&&[2,3,6,8,9,12].includes(p.Sun.house);const moonNight=p.Moon&&[2,3,6,8,9,12].includes(p.Moon.house);if(isNightAsc&&sunNight&&moonNight)return'夜生盘+日月在阴宫';return null},effects:'极度幸运、一生顺利、天生好命',strength:'极强'},
  {id:'parijata',name:'Parijata Yoga',name_cn:'夜来香格局',category:'Special',check:(p)=>{const exaltS={Sun:'Aries',Moon:'Taurus',Mars:'Capricorn',Mercury:'Virgo',Jupiter:'Cancer',Venus:'Pisces',Saturn:'Libra'};const ownS={Sun:['Leo'],Moon:['Cancer'],Mars:['Aries','Scorpio'],Mercury:['Gemini','Virgo'],Jupiter:['Sagittarius','Pisces'],Venus:['Taurus','Libra'],Saturn:['Capricorn','Aquarius']};for(const n of allPlanets){const pl=p[n];if(!pl)continue;if(pl.sign===exaltS[n]||ownS[n]?.includes(pl.sign)){const l=lordOf[pl.sign];if(p[l]&&[1,4,7,10].includes(p[l].house))return`${n}入旺/入庙且其宫主星${l}在角宫`}}return null},effects:'高贵出身、优美人生、享受世界美好',strength:'强'},
  {id:'kahala',name:'Kahala Yoga',name_cn:'勇猛格局',category:'Special',check:(p,asc)=>{const l3=lordOfHouse(asc,3),l9=lordOfHouse(asc,9);if(l3===l9)return null;if(p[l3]&&p[l9]&&p[l3].house===p[l9].house&&[1,4,7,10].includes(p[l3].house))return`3宫主${l3}+9宫主${l9}同宫于角宫`;return null},effects:'勇气与幸运结合、冒险精神带来成功',strength:'强'},
  {id:'sreenatha',name:'Sreenatha Yoga',name_cn:'至尊格局',category:'Special',check:(p,asc)=>{const l7=lordOfHouse(asc,7),l10=lordOfHouse(asc,10);if(l7===l10)return null;if(p[l7]&&[5,9].includes(p[l7].house))return`7宫主${l7}在三角宫`;return null},effects:'配偶地位高、优雅的生活方式',strength:'强'},
  {id:'musa',name:'Musa Yoga',name_cn:'珍珠格局',category:'Special',check:(p)=>{const ven=p.Venus;if(!ven)return null;if(ven.status==='入庙'||ven.status==='入旺'){const l=lordOf[ven.sign];if(p[l]&&[1,4,7,10].includes(p[l].house))return`金星${ven.status}且其宫主星${l}在角宫`}return null},effects:'财富、快乐、享受美好人生',strength:'强'},
  {id:'chaNDali',name:'Chandali Yoga',name_cn:'月蚀格局',category:'Special',check:(p)=>{const m=p.Moon;if(!m)return null;if(p.Rahu&&p.Rahu.house===m.house)return'月亮+Rahu同宫';if(p.Ketu&&p.Ketu.house===m.house)return'月亮+Ketu同宫';return null},effects:'情感波动、情绪不稳定、需灵性修行',strength:'中负',negative:true},
  {id:'grahan',name:'Grahan Yoga',name_cn:'日蚀格局',category:'Special',check:(p)=>{const s=p.Sun;if(!s)return null;if(p.Rahu&&p.Rahu.house===s.house)return'太阳+Rahu同宫';if(p.Ketu&&p.Ketu.house===s.house)return'太阳+Ketu同宫';return null},effects:'自我认同受挑战、权威问题、父亲健康',strength:'中负',negative:true},
  {id:'sarpa',name:'Sarpa Yoga',name_cn:'蛇格局',category:'Special',check:(p)=>{const malefics=['Saturn','Mars','Rahu','Ketu'];for(let h=1;h<=12;h++){const prev=h===1?12:h-1,next=h===12?1:h+1;if(malefics.some(n=>p[n]?.house===prev)&&malefics.some(n=>p[n]?.house===next)){const occ=Object.entries(p).filter(([k,v])=>v.house===h&&!malefics.includes(k));if(occ.length===0)return`第${h}宫被凶星夹且无吉星`}return null}return null},effects:'被夹宫位事务困难、需坚持克服',strength:'中负',negative:true},
  {id:'vasanta',name:'Vasanta Raja Yoga',name_cn:'春日帝王格局',category:'Special',check:(p,asc)=>{const l2=lordOfHouse(asc,2),l5=lordOfHouse(asc,5);if(l2===l5)return null;if(p[l2]&&p[l5]&&p[l2].house===p[l5].house)return`2宫主${l2}+5宫主${l5}同宫`;return null},effects:'财富+创造力结合、投资成功',strength:'强'},
  {id:'saka',name:'Saka Yoga',name_cn:'卓越格局',category:'Special',check:(p,asc)=>{const l4=lordOfHouse(asc,4),l10=lordOfHouse(asc,10);if(l4===l10)return null;if(p[l4]&&p[l10]&&p[l4].house===p[l10].house&&[1,4,7,10].includes(p[l4].house))return`4宫主${l4}+10宫主${l10}同宫于角宫`;return null},effects:'家庭+事业双丰收、社会地位显赫',strength:'强'},
  {id:'amla',name:'Amla Yoga',name_cn:'纯净事业格局',category:'Special',check:(p)=>{const jup=p.Jupiter;if(!jup)return null;if([1,4,7,10].includes(jup.house))return`木星在角宫第${jup.house}宫`;return null},effects:'木星角宫保护事业、道德成功',strength:'中强'},

  // Extra — Combustion & Retrograde Yogas
  {id:'combust_venus',name:'Combust Venus',name_cn:'金星燃烧',category:'Combustion',check:(p)=>{const v=p.Venus;if(!v||!v.combust)return null;return`金星被太阳燃烧(${v.combustDist?.toFixed(1)||''}°)`},effects:'爱情/婚姻受考验、金星事务被削弱',strength:'中负',negative:true},
  {id:'combust_jupiter',name:'Combust Jupiter',name_cn:'木星燃烧',category:'Combustion',check:(p)=>{const j=p.Jupiter;if(!j||!j.combust)return null;return`木星被太阳燃烧(${j.combustDist?.toFixed(1)||''}°)`},effects:'智慧/财富受考验、导师运受阻',strength:'中负',negative:true},
  {id:'retro_saturn',name:'Retrograde Saturn',name_cn:'土星逆行格局',category:'Retrograde',check:(p)=>{const s=p.Saturn;if(!s||!s.retrograde)return null;return'土星逆行'},effects:'前世业力在今生显现、延迟但深化',strength:'中'},
  {id:'retro_jupiter',name:'Retrograde Jupiter',name_cn:'木星逆行格局',category:'Retrograde',check:(p)=>{const j=p.Jupiter;if(!j||!j.retrograde)return null;return'木星逆行'},effects:'内在智慧、非传统导师、灵性深化',strength:'中'},
  {id:'retro_venus',name:'Retrograde Venus',name_cn:'金星逆行格局',category:'Retrograde',check:(p)=>{const v=p.Venus;if(!v||!v.retrograde)return null;return'金星逆行'},effects:'重新审视关系、内在审美、旧爱回归',strength:'中'},

  // Lagna-based strength
  {id:'strong_lagna',name:'Strong Lagna Yoga',name_cn:'强命宫格局',category:'Lagna',check:(p,asc)=>{const l1=lordOfHouse(asc,1);if(p[l1]&&[1,4,7,10].includes(p[l1].house))return`命主星${l1}在角宫第${p[l1].house}宫`;return null},effects:'整体命盘强健、自我意识明确',strength:'强'},
  {id:'lagna_exalted',name:'Exalted Lagna Lord',name_cn:'命主星入旺',category:'Lagna',check:(p,asc)=>{const l1=lordOfHouse(asc,1);if(p[l1]&&p[l1].status==='入旺')return`命主星${l1}入旺`;return null},effects:'命主星极强、整体人生顺利',strength:'极强'},
  {id:'lagna_own',name:'Own Sign Lagna Lord',name_cn:'命主星入庙',category:'Lagna',check:(p,asc)=>{const l1=lordOfHouse(asc,1);if(p[l1]&&p[l1].status==='入庙')return`命主星${l1}入庙`;return null},effects:'命主星稳固、自我感强',strength:'强'},

  // Exchange with Lagna Lord
  {id:'lagna_exchange',name:'Lagna Lord Exchange Yoga',name_cn:'命主星互换格局',category:'Exchange',check:(p,asc)=>{const l1=lordOfHouse(asc,1);for(let h=1;h<=12;h++){const lh=lordOfHouse(asc,h);if(l1===lh)continue;if(p[l1]&&p[lh]&&p[l1].house===h&&p[lh].house===1)return`命主星${l1}与${h}宫主${lh}互换`}return null},effects:'命宫与其他宫完美流通、核心优势',strength:'极强'},
];
