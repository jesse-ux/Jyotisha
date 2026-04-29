/**
 * Jyotish 扩展 Yoga 定义库 (Part 1)
 * 拆分为两个文件避免 token 限制，Part 2 见 yoga-extended-b.js
 */
const signs = ['Aries','Taurus','Gemini','Cancer','Leo','Virgo','Libra','Scorpio','Sagittarius','Capricorn','Aquarius','Pisces'];
const signIdx = s => signs.indexOf(s);
const lordOf = {Aries:'Mars',Taurus:'Venus',Gemini:'Mercury',Cancer:'Moon',Leo:'Sun',Virgo:'Mercury',Libra:'Venus',Scorpio:'Mars',Sagittarius:'Jupiter',Capricorn:'Saturn',Aquarius:'Saturn',Pisces:'Jupiter'};
const lordOfHouse = (asc, h) => lordOf[signs[(signIdx(asc) + h - 1) % 12]];
const allPlanets = ['Sun','Moon','Mars','Mercury','Jupiter','Venus','Saturn'];

export const YOGA_EXTENDED_A = [
  // Pancha Mahapurusha
  {id:'ruchaka',name:'Ruchaka Yoga',name_cn:'光辉格局',category:'Pancha Mahapurusha',check:(p)=>{const m=p.Mars;if(!m||![1,4,7,10].includes(m.house))return null;return(m.status==='入庙'||m.status==='入旺')?`火星在角宫第${m.house}宫且${m.status}`:null},effects:'军事/体育天赋、领导力、勇敢',strength:'极强'},
  {id:'bhadra',name:'Bhadra Yoga',name_cn:'贤明格局',category:'Pancha Mahapurusha',check:(p)=>{const m=p.Mercury;if(!m||![1,4,7,10].includes(m.house))return null;return(m.status==='入庙'||m.status==='入旺')?`水星在角宫第${m.house}宫且${m.status}`:null},effects:'智慧卓越、口才、商业/数学天赋',strength:'极强'},
  {id:'hamsa',name:'Hamsa Yoga',name_cn:'金翼格局',category:'Pancha Mahapurusha',check:(p)=>{const j=p.Jupiter;if(!j||![1,4,7,10].includes(j.house))return null;return(j.status==='入庙'||j.status==='入旺')?`木星在角宫第${j.house}宫且${j.status}`:null},effects:'灵性智慧、道德高尚、教育/法律领袖',strength:'极强'},
  {id:'malavya',name:'Malavya Yoga',name_cn:'美神格局',category:'Pancha Mahapurusha',check:(p)=>{const v=p.Venus;if(!v||![1,4,7,10].includes(v.house))return null;return(v.status==='入庙'||v.status==='入旺')?`金星在角宫第${v.house}宫且${v.status}`:null},effects:'美貌/魅力、艺术天赋、音乐/设计才能',strength:'极强'},
  {id:'sasa',name:'Sasa Yoga',name_cn:'雄威格局',category:'Pancha Mahapurusha',check:(p)=>{const s=p.Saturn;if(!s||![1,4,7,10].includes(s.house))return null;return(s.status==='入庙'||s.status==='入旺')?`土星在角宫第${s.house}宫且${s.status}`:null},effects:'纪律、耐力、建筑/矿业/地产天赋',strength:'极强'},

  // Moon-based
  {id:'gajakesari',name:'Gajakesari Yoga',name_cn:'象狮格局',category:'Moon',check:(p)=>{const m=p.Moon,j=p.Jupiter;if(!m||!j)return null;const d=Math.abs(m.house-j.house);return(d===4||d===8)?`月亮(${m.house}宫)与木星(${j.house}宫)三分`:null},effects:'智慧、品德、教育/法律成功',strength:'强'},
  {id:'amala',name:'Amala Yoga',name_cn:'纯净格局',category:'Moon',check:(p)=>{const m=p.Moon;if(!m)return null;const h10=((m.house+9)%12)+1;const b=['Jupiter','Venus','Mercury'].filter(n=>p[n]?.house===h10);return b.length>0?`月亮后第10宫有吉星${b.join('+')}`:null},effects:'名声清白、受人敬仰',strength:'中强'},
  {id:'adhi_yoga',name:'Adhi Yoga',name_cn:'超前格局',category:'Moon',check:(p)=>{const m=p.Moon;if(!m)return null;const h6=((m.house+5)%12)+1,h7=((m.house+6)%12)+1,h8=((m.house+7)%12)+1;const c=['Jupiter','Venus','Mercury'].filter(n=>[h6,h7,h8].includes(p[n]?.house)).length;return c>=2?`${c}颗吉星在月亮后6/7/8宫`:null},effects:'政治/军事领袖、战胜敌人',strength:'强'},

  // Sun-based
  {id:'veshi',name:'Veshi Yoga',name_cn:'日伴格局',category:'Sun',check:(p)=>{const s=p.Sun;if(!s)return null;const h2=((s.house+1)%12)+1;const pl=allPlanets.filter(n=>n!=='Sun'&&p[n]?.house===h2);return pl.length>0?`太阳后第2宫有${pl.join('+')}`:null},effects:'有追随者、社会影响力',strength:'中'},
  {id:'voshi',name:'Voshi Yoga',name_cn:'日随格局',category:'Sun',check:(p)=>{const s=p.Sun;if(!s)return null;const h12=((s.house+11)%12)+1;const pl=allPlanets.filter(n=>n!=='Sun'&&p[n]?.house===h12);return pl.length>0?`太阳后第12宫有${pl.join('+')}`:null},effects:'乐善好施、精神追求',strength:'中'},
  {id:'ubhayachari',name:'Ubhayachari Yoga',name_cn:'双伴格局',category:'Sun',check:(p)=>{const s=p.Sun;if(!s)return null;const h2=((s.house+1)%12)+1,h12=((s.house+11)%12)+1;const p2=allPlanets.filter(n=>n!=='Sun'&&p[n]?.house===h2);const p12=allPlanets.filter(n=>n!=='Sun'&&p[n]?.house===h12);return(p2.length>0&&p12.length>0)?`太阳两侧都有行星(${p2.join(',')}|${p12.join(',')})`:null},effects:'国王般地位、物质丰盛',strength:'强'},

  // Vipareeta Raja
  {id:'harsha',name:'Harsha Yoga',name_cn:'喜悦反转格局',category:'Vipareeta Raja',check:(p,asc)=>{const l=lordOfHouse(asc,6);return(p[l]&&[6,8,12].includes(p[l].house))?`6宫主${l}落在第${p[l].house}宫`:null},effects:'敌人瓦解、健康恢复',strength:'强'},
  {id:'sarala',name:'Sarala Yoga',name_cn:'明净反转格局',category:'Vipareeta Raja',check:(p,asc)=>{const l=lordOfHouse(asc,8);return(p[l]&&[6,8,12].includes(p[l].house))?`8宫主${l}落在第${p[l].house}宫`:null},effects:'从危机崛起、长寿、隐藏财富',strength:'强'},
  {id:'vimala',name:'Vimala Yoga',name_cn:'纯净反转格局',category:'Vipareeta Raja',check:(p,asc)=>{const l=lordOfHouse(asc,12);return(p[l]&&[6,8,12].includes(p[l].house))?`12宫主${l}落在第${p[l].house}宫`:null},effects:'支出减少、灵性提升、海外成功',strength:'强'},

  // Raja Yogas
  {id:'raja_kt',name:'Raja Yoga',name_cn:'帝王格局',category:'Raja Yoga',check:(p,asc)=>{const tl=[lordOfHouse(asc,5),lordOfHouse(asc,9)];const kl=[lordOfHouse(asc,1),lordOfHouse(asc,4),lordOfHouse(asc,7),lordOfHouse(asc,10)];for(const t of tl){if(kl.includes(t))continue;if(p[t]&&[1,4,7,10].includes(p[t].house))return`三角宫主${t}落入角宫第${p[t].house}宫`;for(const k of kl){if(t!==k&&p[t]&&p[k]&&p[t].house===p[k].house)return`三角宫主${t}+角宫主${k}同宫`}}return null},effects:'权力、地位、领导才能',strength:'极强'},
  {id:'dk_adhipati',name:'Dharma-Karmadhipati Yoga',name_cn:'法业双主格局',category:'Raja Yoga',check:(p,asc)=>{const l9=lordOfHouse(asc,9),l10=lordOfHouse(asc,10);if(l9===l10)return null;if(p[l9]&&p[l10]&&p[l9].house===p[l10].house)return`9宫主${l9}+10宫主${l10}同宫`;return null},effects:'正道获得事业成功、道德与财富兼备',strength:'极强'},

  // Parivartana
  {id:'maha_pariv',name:'Maha Parivartana Yoga',name_cn:'大互换格局',category:'Parivartana',check:(p,asc)=>{const pairs=[[1,2],[1,3],[1,4],[1,5],[1,7],[1,9],[1,10],[1,11],[2,5],[4,5],[4,9],[4,10],[5,9],[5,11],[9,10],[9,11],[10,11]];for(const[a,b]of pairs){const la=lordOfHouse(asc,a),lb=lordOfHouse(asc,b);if(la===lb)continue;if(p[la]&&p[lb]&&p[la].house===b&&p[lb].house===a)return`${a}宫主${la}与${b}宫主${lb}互换`}return null},effects:'两宫能量完美流通',strength:'强'},
  {id:'dainya_pariv',name:'Dainya Parivartana Yoga',name_cn:'凶互换格局',category:'Parivartana',check:(p,asc)=>{for(const d of[6,8,12]){const ld=lordOfHouse(asc,d);for(let h=1;h<=12;h++){if(h===d)continue;const lh=lordOfHouse(asc,h);if(ld===lh)continue;if(p[ld]&&p[lh]&&p[ld].house===h&&p[lh].house===d)return`${d}宫主${ld}与${h}宫主${lh}互换（凶互换）`}}return null},effects:'凶宫事务带来意外后果',strength:'中负',negative:true},

  // Neechabhanga
  {id:'neechabhanga',name:'Neechabhanga Raja Yoga',name_cn:'落陷取消格局',category:'Cancellation',check:(p,asc)=>{const debS={Sun:'Libra',Moon:'Scorpio',Mars:'Cancer',Mercury:'Pisces',Jupiter:'Capricorn',Venus:'Virgo',Saturn:'Aries'};const exaltS={Sun:'Aries',Moon:'Taurus',Mars:'Capricorn',Mercury:'Virgo',Jupiter:'Cancer',Venus:'Pisces',Saturn:'Libra'};for(const n of allPlanets){const pl=p[n];if(!pl||pl.sign!==debS[n])continue;const dl=lordOf[debS[n]];const cancels=[];if(p[dl]&&[1,4,7,10].includes(p[dl].house))cancels.push(`${dl}在角宫`);if(p[dl]&&p[dl].sign===pl.sign)cancels.push(`${dl}同宫`);const el=lordOf[exaltS[n]];if(p[el]&&[1,4,7,10].includes(p[el].house))cancels.push(`${el}(入旺主)在角宫`);if(cancels.length>0)return`${n}落陷但被${cancels.join('、')}取消`}return null},effects:'早年困境后崛起、逆袭人生',strength:'极强'},

  // Kartari
  {id:'shubh_kartari',name:'Shubha Kartari Yoga',name_cn:'吉剪格局',category:'Kartari',check:(p)=>{const b=['Jupiter','Venus','Mercury','Moon'];for(let h=1;h<=12;h++){const prev=h===1?12:h-1,next=h===12?1:h+1;if(b.some(n=>p[n]?.house===prev)&&b.some(n=>p[n]?.house===next))return`第${h}宫被吉星夹护`}return null},effects:'被保护宫位事务顺遂',strength:'中强'},
  {id:'papa_kartari',name:'Papa Kartari Yoga',name_cn:'凶剪格局',category:'Kartari',check:(p)=>{const m=['Saturn','Mars','Sun','Rahu','Ketu'];for(let h=1;h<=12;h++){const prev=h===1?12:h-1,next=h===12?1:h+1;if(m.some(n=>p[n]?.house===prev)&&m.some(n=>p[n]?.house===next))return`第${h}宫被凶星夹攻`}return null},effects:'被夹攻宫位事务受阻',strength:'中负',negative:true},

  // Planetary Pairs
  {id:'sun_mars',name:'Sun-Mars Yoga',name_cn:'日火格局',category:'Pair',check:(p)=>p.Sun?.house===p.Mars?.house?'太阳+火星同宫':null,effects:'意志力强、领导力、竞争精神',strength:'中强'},
  {id:'sun_jupiter',name:'Sun-Jupiter Yoga',name_cn:'日木格局',category:'Pair',check:(p)=>p.Sun?.house===p.Jupiter?.house?'太阳+木星同宫':null,effects:'智慧、道德、教育/法律成功',strength:'强'},
  {id:'sun_venus',name:'Sun-Venus Yoga',name_cn:'日金格局',category:'Pair',check:(p)=>p.Sun?.house===p.Venus?.house?'太阳+金星同宫':null,effects:'艺术天赋、魅力（查燃烧）',strength:'中'},
  {id:'sun_saturn',name:'Sun-Saturn Yoga',name_cn:'日土格局',category:'Pair',check:(p)=>p.Sun?.house===p.Saturn?.house?'太阳+土星同宫':null,effects:'权威+纪律、父亲关系紧张',strength:'中'},
  {id:'moon_mercury',name:'Moon-Mercury Yoga',name_cn:'月水格局',category:'Pair',check:(p)=>p.Moon?.house===p.Mercury?.house?'月亮+水星同宫':null,effects:'智商高、口才、写作天赋',strength:'中'},
  {id:'moon_jupiter',name:'Moon-Jupiter Yoga',name_cn:'月木格局',category:'Pair',check:(p)=>p.Moon?.house===p.Jupiter?.house?'月亮+木星同宫':null,effects:'灵性智慧、善良、教育天赋',strength:'强'},
  {id:'moon_saturn',name:'Moon-Saturn Yoga',name_cn:'月土格局',category:'Pair',check:(p)=>p.Moon?.house===p.Saturn?.house?'月亮+土星同宫':null,effects:'情绪压抑、责任感重',strength:'中负',negative:true},
  {id:'moon_venus',name:'Moon-Venus Yoga',name_cn:'月金格局',category:'Pair',check:(p)=>p.Moon?.house===p.Venus?.house?'月亮+金星同宫':null,effects:'艺术品味、浪漫、社交魅力',strength:'中'},
  {id:'mars_mercury',name:'Mars-Mercury Yoga',name_cn:'火水格局',category:'Pair',check:(p)=>p.Mars?.house===p.Mercury?.house?'火星+水星同宫':null,effects:'分析力+行动力、技术天赋',strength:'中'},
  {id:'mars_jupiter',name:'Mars-Jupiter Yoga',name_cn:'火木格局',category:'Pair',check:(p)=>p.Mars?.house===p.Jupiter?.house?'火星+木星同宫':null,effects:'正义感、教育/军事/法律',strength:'强'},
  {id:'mars_saturn',name:'Mars-Saturn Yoga',name_cn:'火土格局',category:'Pair',check:(p)=>p.Mars?.house===p.Saturn?.house?'火星+土星同宫':null,effects:'行动受阻但极端耐力',strength:'中负',negative:true},
  {id:'mercury_jupiter',name:'Mercury-Jupiter Yoga',name_cn:'水木格局',category:'Pair',check:(p)=>p.Mercury?.house===p.Jupiter?.house?'水星+木星同宫':null,effects:'学术天才、语言/教学天赋',strength:'强'},
  {id:'mercury_venus',name:'Mercury-Venus Yoga',name_cn:'水金格局',category:'Pair',check:(p)=>p.Mercury?.house===p.Venus?.house?'水星+金星同宫':null,effects:'艺术+智力、设计/音乐/商业',strength:'中强'},
  {id:'mercury_saturn',name:'Mercury-Saturn Yoga',name_cn:'水土格局',category:'Pair',check:(p)=>p.Mercury?.house===p.Saturn?.house?'水星+土星同宫':null,effects:'深度思考、数学/科学研究',strength:'中'},
  {id:'venus_saturn',name:'Venus-Saturn Yoga',name_cn:'金土格局',category:'Pair',check:(p)=>p.Venus?.house===p.Saturn?.house?'金星+土星同宫':null,effects:'延迟满足的爱情、成熟美学',strength:'中'},

  // Status
  {id:'exalted',name:'Exalted Planet Yoga',name_cn:'入旺格局',category:'Status',check:(p)=>{const e=allPlanets.filter(n=>p[n]?.status==='入旺');return e.length>=1?`${e.join('、')}入旺`:null},effects:'入旺行星极大增强相关事务',strength:'强'},
  {id:'multi_own',name:'Multiple Own Sign Yoga',name_cn:'多入庙格局',category:'Status',check:(p)=>{const o=allPlanets.filter(n=>p[n]?.status==='入庙');return o.length>=2?`${o.join('、')}入庙`:null},effects:'多行星入庙带来全面力量',strength:'强'},
  {id:'multi_deb',name:'Multiple Debilitated Yoga',name_cn:'多落陷格局',category:'Status',check:(p)=>{const d=allPlanets.filter(n=>p[n]?.status==='入陷');return d.length>=2?`${d.join('、')}落陷`:null},effects:'多行星落陷事务受阻',strength:'中负',negative:true},
];
