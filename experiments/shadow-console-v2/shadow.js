(() => {
'use strict';

const DATA = window.__SHADOW_DATA__;
const STORAGE_KEY = 'kajitori_shadow_v2';
const LAYERS = ['now', 'today', 'routine', 'review'];
const LAYER_LABEL = { now: '今見る', today: '今日の候補', routine: 'ルーティン', review: 'レビュー' };
const LAYER_RANK = { now: 0, today: 1, routine: 2, review: 3 };
const PRIORITY_RANK = { safety_health_deadline: 0, safety_health: 1, deadline: 2, capacity: 3, high: 4, essential_routine: 5, maintenance: 6 };
const PASS_STATUSES = new Set(['PASS_DIRECT', 'PASS_WITH_BOUNDARY']);
const SOURCE_LABEL = { self: '自分で気づいた', partner: 'パートナーから自然に言われた', daycare: '園・学校', calendar: '予定・締切', stock: '在庫・物の状態', environment: '家・天候・移動', other: 'その他' };

const CATALOG = new Map(DATA.catalog.map(x => [x.id, x]));
const REVIEW = new Map(DATA.review.items.map(x => [x.id, x]));
const BOUNDARIES = new Map(DATA.boundaries.items.map(x => [x.id, x]));
const BUNDLES = DATA.bundles.rules;
const RULES_BY_ITEM = new Map();
for (const rule of DATA.rules.rules) {
  for (const emission of rule.emit) {
    if (!RULES_BY_ITEM.has(emission.id)) RULES_BY_ITEM.set(emission.id, []);
    RULES_BY_ITEM.get(emission.id).push({ rule, emission });
  }
}

const QUICK_FIELDS = [
  {group:'園・予定', id:'daycare_today', label:'今日は登園日', path:'daycare.attendance_today', type:'tri'},
  {group:'園・予定', id:'daycare_tomorrow', label:'明日は登園日', path:'daycare.attendance_tomorrow', type:'tri'},
  {group:'園・予定', id:'daycare_unread', label:'園から未読の連絡がある', path:'daycare.unread_notice', type:'tri'},
  {group:'園・予定', id:'daycare_prep', label:'明日の登園準備は完了', path:'daycare.tomorrow_prep_complete', type:'tri'},
  {group:'園・予定', id:'daycare_deadline', label:'園の最短締切まで（時間）', path:'daycare.deadline_within_hours', type:'number', min:0, max:720},
  {group:'園・予定', id:'vaccination_hours', label:'予防接種まで（時間）', path:'events.vaccination.appointment_within_hours', type:'number', min:0, max:720, derive:'vaccination'},
  {group:'園・予定', id:'vaccination_prep', label:'予防接種の準備は完了', path:'events.vaccination.prep_complete', type:'tri'},
  {group:'園・予定', id:'admin_deadline', label:'行政・書類の最短締切まで（時間）', path:'household.admin.deadline_within_hours', type:'number', min:0, max:2160},

  {group:'赤ちゃん', id:'milk_stock', label:'ミルク在庫', path:'children.infant.feeding.milk_stock', type:'select', options:[['','未確認'],['ok','十分'],['low','少ない'],['critical','次の購入機会まで持たない']]},
  {group:'赤ちゃん', id:'clean_bottles', label:'清潔な哺乳瓶', path:'children.infant.feeding.clean_bottles', type:'select', options:[['','未確認'],['ok','足りる'],['low','少ない'],['critical','足りない']]},
  {group:'赤ちゃん', id:'night_set', label:'夜間セットは準備済み', path:'children.infant.feeding.night_set_ready', type:'tri'},
  {group:'赤ちゃん', id:'diaper_stock', label:'オムツ在庫', path:'children.infant.diaper.stock', type:'select', options:[['','未確認'],['ok','十分'],['low','少ない'],['critical','次の購入機会まで持たない']]},
  {group:'赤ちゃん', id:'wipes_stock', label:'おしりふき在庫', path:'children.infant.diaper.wipes_stock', type:'select', options:[['','未確認'],['ok','十分'],['low','少ない'],['critical','足りない']]},
  {group:'赤ちゃん', id:'elimination_changed', label:'尿・便にいつもとの差がある', path:'children.infant.diaper.elimination_changed', type:'tri', derive:'observed_elimination'},
  {group:'赤ちゃん', id:'skin_changed', label:'皮膚・オムツかぶれに変化がある', path:'children.infant.diaper.skin_changed', type:'tri'},
  {group:'赤ちゃん', id:'symptom_changed', label:'発熱・咳・嘔吐などに変化がある', path:'children.infant.health.symptom_changed', type:'tri', derive:'observed_symptom'},
  {group:'赤ちゃん', id:'bath_prep', label:'入浴前のタオル・着替え・保湿準備は完了', path:'children.infant.hygiene.bath_prep_ready', type:'tri'},

  {group:'家の運営', id:'dinner_decided', label:'夕食の方針は決まっている', path:'household.food.dinner_plan_decided', type:'tri'},
  {group:'家の運営', id:'expiring_food', label:'早めに使う食材がある', path:'household.food.expiring_items', type:'tri'},
  {group:'家の運営', id:'sink_blocked', label:'シンクが次の食事を妨げる状態', path:'household.kitchen.sink_blocked', type:'tri'},
  {group:'家の運営', id:'laundry_urgent', label:'今日優先する洗濯物がある', path:'household.laundry.urgent_items_pending', type:'tri'},
  {group:'家の運営', id:'dry_items', label:'乾いた洗濯物の次工程が残っている', path:'household.laundry.dry_items_pending', type:'tri'},
  {group:'家の運営', id:'floor_hazard', label:'床に小物・誤飲物がある', path:'household.safety.floor_hazard_present', type:'tri'},
  {group:'家の運営', id:'waste_hours', label:'次のごみ回収まで（時間）', path:'household.waste.collection_within_hours', type:'number', min:0, max:720},
  {group:'家の運営', id:'waste_ready', label:'ごみ出し準備は完了', path:'household.waste.ready', type:'tri'},
  {group:'家の運営', id:'tomorrow_open', label:'明日の予定に未確認がある', path:'household.planning.tomorrow_open', type:'tri'},
  {group:'家の運営', id:'handoff_due', label:'交代相手への引継ぎが必要', path:'family.handoff_due', type:'tri'},
  {group:'家の運営', id:'fatigue_high', label:'夫婦どちらか・両方の疲労が強い', path:'family.adult_fatigue_high', type:'tri'},
  {group:'家の運営', id:'rebalance', label:'今日の計画を組み直す必要がある', path:'family.plan_needs_rebalance', type:'tri'},

  {group:'外出・天候', id:'outing_planned', label:'子どもとの外出予定がある', path:'context.outing.planned', type:'tri', derive:'outing'},
  {group:'外出・天候', id:'outing_car', label:'車を使う', path:'context.outing.car_used', type:'tri'},
  {group:'外出・天候', id:'outing_stroller', label:'ベビーカーを使う', path:'context.outing.stroller_used', type:'tri'},
  {group:'外出・天候', id:'outing_hazard', label:'道路・駐車場・階段など具体的な注意箇所がある', path:'context.outing.hazard_context_available', type:'tri'},
  {group:'外出・天候', id:'official_heat', label:'公式の熱中症警戒・高い暑さ指数を確認した', path:'context.weather.official_heat_alert_or_high_wbgt', type:'tri'},
  {group:'外出・天候', id:'official_winter', label:'公式の大雪・暴風雪情報を確認した', path:'context.weather.official_snow_or_blizzard_warning', type:'tri'}
];

const main = document.getElementById('main');
const modal = document.getElementById('modal');
const modalTitle = document.getElementById('modalTitle');
const modalBody = document.getElementById('modalBody');
let activeView = 'today';
let toastTimer = null;
let store = loadStore();

function uid(prefix='id') {
  if (crypto.randomUUID) return `${prefix}-${crypto.randomUUID()}`;
  return `${prefix}-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}
function localDate() {
  const d = new Date();
  const p = n => String(n).padStart(2,'0');
  return `${d.getFullYear()}-${p(d.getMonth()+1)}-${p(d.getDate())}`;
}
function nowIso() { return new Date().toISOString(); }
function esc(value) { return String(value ?? '').replace(/[&<>"']/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch])); }
function clone(value) { return JSON.parse(JSON.stringify(value)); }
function getPath(data, path) {
  let cur = data;
  for (const part of path.split('.')) {
    if (!cur || typeof cur !== 'object' || !(part in cur)) return {found:false, value:undefined};
    cur = cur[part];
  }
  return {found:true, value:cur};
}
function setPath(data, path, value) {
  const parts = path.split('.');
  let cur = data;
  for (let i=0;i<parts.length-1;i++) {
    if (!cur[parts[i]] || typeof cur[parts[i]] !== 'object') cur[parts[i]] = {};
    cur = cur[parts[i]];
  }
  cur[parts[parts.length-1]] = value;
}
function deletePath(data, path) {
  const parts = path.split('.');
  let cur = data;
  for (let i=0;i<parts.length-1;i++) {
    if (!cur || typeof cur !== 'object' || !(parts[i] in cur)) return;
    cur = cur[parts[i]];
  }
  if (cur && typeof cur === 'object') delete cur[parts[parts.length-1]];
}
function loadStore() {
  try {
    const parsed = JSON.parse(localStorage.getItem(STORAGE_KEY));
    if (parsed && parsed.version === 2) return parsed;
  } catch (_) {}
  return {version:2, profile:{initialized:false,tags:['household','has_child'],config:{},updatedAt:null},days:{},audit:[]};
}
function saveStore(action, detail={}) {
  store.audit.push({id:uid('audit'),at:nowIso(),action,detail});
  if (store.audit.length > 1000) store.audit = store.audit.slice(-1000);
  localStorage.setItem(STORAGE_KEY, JSON.stringify(store));
  render();
}
function day() {
  const key = localDate();
  if (!store.days[key]) {
    store.days[key] = {dayId:uid('day'),date:key,phase:'setup',rawState:{date:key,context:{day_active:true,time_block:timeBlock()}},engineSnapshot:null,actualLogs:[],actualLogConfirmedAt:null,cardReviews:{},revealedAt:null,observations:[],explicitNoAdditional:false};
    localStorage.setItem(STORAGE_KEY, JSON.stringify(store));
  }
  return store.days[key];
}
function timeBlock() {
  const h = new Date().getHours();
  if (h < 6) return 'night';
  if (h < 12) return 'morning';
  if (h < 17) return 'afternoon';
  return 'evening';
}
function showToast(text) {
  const el = document.getElementById('toast');
  el.textContent = text; el.classList.add('show');
  clearTimeout(toastTimer); toastTimer=setTimeout(()=>el.classList.remove('show'),2400);
}
function openModal(title, html, after) {
  modalTitle.textContent = title; modalBody.innerHTML = html; modal.classList.add('show'); modal.setAttribute('aria-hidden','false');
  if (after) after();
}
function closeModal() { modal.classList.remove('show'); modal.setAttribute('aria-hidden','true'); }

function profileCapabilities(profile) {
  const caps = new Set(profile.tags || []);
  for (const [key,value] of Object.entries(profile.config || {})) if (value === true) caps.add(key);
  return caps;
}
function profileGate(rule, state) {
  const caps = profileCapabilities(store.profile);
  const missingTags = (rule.profile_all_tags || []).filter(tag => !caps.has(tag));
  if (missingTags.length) return {ok:false, reason:'profile_tag', missing:missingTags};
  const runtime = state.profile_runtime || {};
  for (const [key,expected] of Object.entries(rule.profile_config_equals || {})) {
    const hasRuntime = Object.prototype.hasOwnProperty.call(runtime,key);
    const hasConfig = Object.prototype.hasOwnProperty.call(store.profile.config || {},key);
    if (!hasRuntime && !hasConfig) return {ok:false,reason:'profile_config_missing',missing:[key]};
    const actual = hasRuntime ? runtime[key] : store.profile.config[key];
    if (actual !== expected) return {ok:false,reason:'profile_config_mismatch',missing:[key]};
  }
  return {ok:true,missing:[]};
}
function evalLeaf(node, state, diagnostics) {
  const found = getPath(state,node.path);
  diagnostics.paths.add(node.path);
  if (!found.found) diagnostics.missing.add(node.path);
  const op=node.op, actual=found.value, expected=node.value;
  if (op==='exists') return found.found && actual != null;
  if (op==='not_exists') return !found.found || actual == null;
  if (!found.found) return false;
  if (op==='truthy') return Boolean(actual);
  if (op==='falsy') return !Boolean(actual);
  if (op==='eq') return actual===expected;
  if (op==='ne') return actual!==expected;
  if (op==='in') return Array.isArray(expected) && expected.includes(actual);
  if (op==='not_in') return Array.isArray(expected) && !expected.includes(actual);
  if (op==='lt') return actual<expected;
  if (op==='lte') return actual<=expected;
  if (op==='gt') return actual>expected;
  if (op==='gte') return actual>=expected;
  if (op==='contains') return actual != null && typeof actual.includes==='function' && actual.includes(expected);
  if (op==='intersects') return Array.isArray(actual) && Array.isArray(expected) && actual.some(x=>expected.includes(x));
  throw new Error(`unsupported op ${op}`);
}
function evalCondition(node,state,diagnostics={paths:new Set(),missing:new Set()}) {
  if (node.all) return node.all.every(child=>evalCondition(child,state,diagnostics));
  if (node.any) return node.any.some(child=>evalCondition(child,state,diagnostics));
  if (node.not) return !evalCondition(node.not,state,diagnostics);
  return evalLeaf(node,state,diagnostics);
}
function healthGate(item,state) {
  if (!(item.type || '').split('/').includes('S')) return {ok:true};
  const gate=REVIEW.get(item.id);
  if (!gate) return {ok:false,reason:'missing_manual_review'};
  if (!PASS_STATUSES.has(gate.status)) return {ok:false,reason:`review_status:${gate.status}`};
  const missingSources=(gate.required_source_ids||[]).filter(id=>!(item.source_ids||[]).includes(id));
  if (missingSources.length) return {ok:false,reason:'missing_required_sources',missingSources};
  if (gate.status==='PASS_WITH_BOUNDARY') {
    const boundary=BOUNDARIES.get(item.id);
    if (!boundary) return {ok:false,reason:'missing_boundary_definition'};
    const missing=(boundary.required_context_paths||[]).filter(path=>{const x=getPath(state,path);return !x.found||x.value==null;});
    if (missing.length) return {ok:false,reason:'missing_boundary_input',missingPaths:missing};
  }
  return {ok:true};
}
function derive(state) {
  const candidates=new Map(), suppressed=[];
  const audit={ruleCount:DATA.rules.rules.length,profileBlocked:0,conditionFalse:0,fired:0};
  for (const rule of DATA.rules.rules) {
    const pg=profileGate(rule,state);
    if (!pg.ok) {audit.profileBlocked++;continue;}
    const diag={paths:new Set(),missing:new Set()};
    if (!evalCondition(rule.when,state,diag)) {audit.conditionFalse++;continue;}
    audit.fired++;
    const bundle=BUNDLES[rule.rule_id];
    for (const emission of rule.emit) {
      const item=CATALOG.get(emission.id);
      const gate=healthGate(item,state);
      if (!gate.ok) {suppressed.push({itemId:item.id,ruleId:rule.rule_id,layer:emission.layer,...gate});continue;}
      const contribution={ruleId:rule.rule_id,layer:emission.layer,reason:emission.reason,bundleId:bundle.bundle_id,bundleLabel:bundle.label,bundleClose:bundle.close_condition};
      let entry=candidates.get(item.id);
      if (!entry) {
        entry={id:item.id,label:item.label,type:item.type,domain:item.domain,priorityClass:item.priority_class,sourceIds:item.source_ids||[],isHealthSafety:(item.type||'').split('/').includes('S'),layer:emission.layer,primaryRuleId:rule.rule_id,primaryBundleId:bundle.bundle_id,primaryBundleLabel:bundle.label,primaryBundleClose:bundle.close_condition,contributions:[contribution]};
        candidates.set(item.id,entry);
      } else {
        entry.contributions.push(contribution);
        if (LAYER_RANK[emission.layer] < LAYER_RANK[entry.layer]) {
          entry.layer=emission.layer;entry.primaryRuleId=rule.rule_id;entry.primaryBundleId=bundle.bundle_id;entry.primaryBundleLabel=bundle.label;entry.primaryBundleClose=bundle.close_condition;
        }
      }
    }
  }
  const atomic=[...candidates.values()];
  atomic.sort((a,b)=>LAYER_RANK[a.layer]-LAYER_RANK[b.layer]||(PRIORITY_RANK[a.priorityClass]??99)-(PRIORITY_RANK[b.priorityClass]??99)||a.domain.localeCompare(b.domain)||a.id.localeCompare(b.id));
  const groups=new Map();
  for (const item of atomic) {
    const key=`${item.layer}:${item.primaryBundleId}`;
    if (!groups.has(key)) groups.set(key,{cardId:key,layer:item.layer,bundleId:item.primaryBundleId,label:item.primaryBundleLabel,closeCondition:item.primaryBundleClose,atomicIds:[],atomicLabels:[],domains:new Set(),containsHealthSafety:false,reasons:new Set(),priorityRank:99,attentionClass:'maintenance'});
    const card=groups.get(key);card.atomicIds.push(item.id);card.atomicLabels.push(item.label);card.domains.add(item.domain);card.containsHealthSafety ||= item.isHealthSafety;card.priorityRank=Math.min(card.priorityRank,PRIORITY_RANK[item.priorityClass]??99);if ((PRIORITY_RANK[item.priorityClass]??99)===card.priorityRank) card.attentionClass=item.priorityClass;for(const c of item.contributions)card.reasons.add(c.reason);
  }
  const cards=[...groups.values()].map(c=>({...c,domains:[...c.domains].sort(),reasons:[...c.reasons].sort()}));
  cards.sort((a,b)=>LAYER_RANK[a.layer]-LAYER_RANK[b.layer]||a.priorityRank-b.priorityRank||a.label.localeCompare(b.label));
  return {generatedAt:nowIso(),atomic,cards,suppressed,ruleAudit:audit,counts:Object.fromEntries(LAYERS.map(layer=>[layer,atomic.filter(x=>x.layer===layer).length])),cardCounts:Object.fromEntries(LAYERS.map(layer=>[layer,cards.filter(x=>x.layer===layer).length]))};
}

async function sha256(text) {
  const buf=await crypto.subtle.digest('SHA-256',new TextEncoder().encode(text));
  return [...new Uint8Array(buf)].map(x=>x.toString(16).padStart(2,'0')).join('');
}
function prepareState(raw) {
  const state=clone(raw||{});
  state.date=localDate();
  setPath(state,'context.day_active',true);
  setPath(state,'context.time_block',timeBlock());
  setPath(state,'profile_runtime.bottle_used',Boolean(store.profile.config.bottle_used));
  if (store.profile.config.local_area_set) setPath(state,'household.local_area_set',true);
  return state;
}
function applyDerived(field,value,state) {
  if (field.derive==='vaccination' && value !== '') {
    const hours=Number(value);const when=new Date(Date.now()+hours*3600000).toISOString();
    setPath(state,'events.vaccination.due_candidate',true);
    setPath(state,'events.vaccination.schedule_source_confirmed',true);
    setPath(state,'events.vaccination.history_available',true);
    setPath(state,'events.vaccination.booking_status','booked');
    setPath(state,'events.vaccination.booking_rule_available',true);
    setPath(state,'events.vaccination.appointment_at',when);
    setPath(state,'events.vaccination.provider_instructions_available',true);
    setPath(state,'events.medical.appointment_within_hours',hours);
    setPath(state,'events.medical.prep_complete',Boolean(getPath(state,'events.vaccination.prep_complete').value));
  }
  if (field.derive==='observed_elimination' && value===true) setPath(state,'children.infant.diaper.observed_at',nowIso());
  if (field.derive==='observed_symptom' && value===true) {
    setPath(state,'children.infant.health.observed_condition_available',true);
    setPath(state,'children.infant.health.observed_at',nowIso());
  }
  if (field.derive==='outing' && value===true) {
    setPath(state,'context.outing.with_child',true);
    setPath(state,'context.outing.with_infant',Boolean(store.profile.config.infant));
    setPath(state,'context.outing.transport_context_available',true);
  }
}
function readFieldValue(field) {
  const el=document.querySelector(`[data-field-id="${field.id}"]`);
  if (!el) return {known:false};
  if (field.type==='tri') {
    const v=el.dataset.value;
    if (v==='yes') return {known:true,value:true};
    if (v==='no') return {known:true,value:false};
    return {known:false};
  }
  if (field.type==='number') {
    if (el.value==='') return {known:false};
    return {known:true,value:Number(el.value)};
  }
  if (field.type==='select') {
    if (el.value==='') return {known:false};
    return {known:true,value:el.value};
  }
  return {known:false};
}
function collectIntake() {
  const state={date:localDate(),context:{day_active:true,time_block:timeBlock()}};
  for (const field of QUICK_FIELDS) {
    const answer=readFieldValue(field);
    if (!answer.known) continue;
    setPath(state,field.path,answer.value);
    applyDerived(field,answer.value,state);
  }
  const dayObj=day();
  dayObj.rawState=prepareState(state);
  dayObj.rawStateCapturedAt=nowIso();
  return dayObj.rawState;
}
function renderField(field,raw) {
  const existing=getPath(raw,field.path);
  if (field.type==='tri') {
    const current=!existing.found?'unknown':existing.value===true?'yes':'no';
    return `<div class="field"><span class="label">${esc(field.label)}</span><div class="tri" data-field-id="${esc(field.id)}" data-value="${current}"><button type="button" data-tri="unknown" class="${current==='unknown'?'active':''}">未回答</button><button type="button" data-tri="yes" class="${current==='yes'?'active':''}">はい</button><button type="button" data-tri="no" class="${current==='no'?'active':''}">いいえ</button></div></div>`;
  }
  if (field.type==='select') {
    return `<div class="field"><label for="f-${esc(field.id)}">${esc(field.label)}</label><select id="f-${esc(field.id)}" data-field-id="${esc(field.id)}">${field.options.map(([v,l])=>`<option value="${esc(v)}" ${existing.found&&String(existing.value)===String(v)?'selected':''}>${esc(l)}</option>`).join('')}</select></div>`;
  }
  return `<div class="field"><label for="f-${esc(field.id)}">${esc(field.label)}</label><input id="f-${esc(field.id)}" data-field-id="${esc(field.id)}" type="number" min="${field.min??0}" max="${field.max??9999}" value="${existing.found?esc(existing.value):''}" inputmode="decimal"></div>`;
}
function bindTri() {
  document.querySelectorAll('.tri').forEach(group=>group.querySelectorAll('button').forEach(btn=>btn.addEventListener('click',()=>{group.dataset.value=btn.dataset.tri;group.querySelectorAll('button').forEach(b=>b.classList.toggle('active',b===btn));})));
}

function renderToday() {
  const d=day();
  if (!store.profile.initialized) return `<div class="stack"><article class="card phase-card"><h3>最初に家庭条件を設定</h3><p>候補の母集団を絞るための機能設定です。記録はこの端末だけに保存されます。</p><button class="primary" id="openProfile" type="button">家庭設定を始める</button></article></div>`;
  if (d.phase==='setup') {
    const groups=[...new Set(QUICK_FIELDS.map(x=>x.group))];
    return `<section class="section"><div class="section-head"><h2>朝の既知状態</h2><span>未回答は「不明」のまま</span></div><article class="card"><p class="notice">全部埋める必要はありません。確認できた事実だけ入力し、未回答を「問題なし」とは扱いません。</p>${groups.map((group,i)=>`<details ${i===0?'open':''}><summary>${esc(group)}</summary><div class="details-body">${QUICK_FIELDS.filter(x=>x.group===group).map(x=>renderField(x,d.rawState||{})).join('')}</div></details>`).join('<div style="height:8px"></div>')}<div class="row-actions single"><button class="primary" id="sealBtn" type="button">候補を生成して封印</button></div></article></section>`;
  }
  const snap=d.engineSnapshot;
  if (d.phase==='sealed') {
    return `<div class="stack"><article class="card phase-card"><div class="seal"><div class="seal-icon">✓</div><div class="seal-copy"><strong>候補は封印済み</strong><span>${esc(snap.generatedAt)} ・ ${esc(snap.hash.slice(0,16))}…</span></div></div><p>内容・件数は夜の照合まで表示しません。普段どおり生活し、必要事項が起きたら「実際に起きた」へ記録してください。</p><div class="row-actions"><button class="secondary" id="goActual" type="button">実際に起きたこと</button><button class="ghost" id="revealStart" type="button">夜の照合へ</button></div></article><article class="card"><h3>封印の意味</h3><p>先に提案を見ると行動が変わり、「本来自分で気づけたか」を測れません。健康・安全・締切対応は封印とは無関係に普段どおり行ってください。</p></article></div>`;
  }
  return renderReveal();
}
function renderReveal() {
  const d=day(), snap=d.engineSnapshot;
  return `<section class="section"><div class="section-head"><h2>夜の照合</h2><span>${snap.payload.cards.length}カード / ${snap.payload.atomic.length}責任</span></div><div class="stack">${snap.payload.cards.map(card=>renderCandidateCard(card,d.cardReviews[card.cardId]||{})).join('')||'<div class="empty">候補カードはありませんでした。</div>'}</div></section>`;
}
function renderCandidateCard(card,review) {
  return `<article class="candidate-card ${card.containsHealthSafety?'health':''}" data-card-id="${esc(card.cardId)}"><div class="phase-row"><span class="phase-pill">${esc(LAYER_LABEL[card.layer])}</span>${card.containsHealthSafety?'<span class="tag warn">健康・安全を含む</span>':''}</div><h3>${esc(card.label)}</h3><p>${esc(card.closeCondition)}</p><ul class="atomic-list">${card.atomicLabels.map(x=>`<li>${esc(x)}</li>`).join('')}</ul><div class="field" style="margin-top:11px"><span class="label">このカードは実際に必要だった？</span><div class="review-grid" data-review="needed"><button type="button" data-value="yes" class="${review.needed==='yes'?'active':''}">必要</button><button type="button" data-value="no" class="${review.needed==='no'?'active':''}">不要</button><button type="button" data-value="unsure" class="${review.needed==='unsure'?'active':''}">判断不能</button></div></div><div class="field"><span class="label">タイミング</span><div class="review-grid" data-review="timing"><button type="button" data-value="right" class="${review.timing==='right'?'active':''}">適切</button><button type="button" data-value="early" class="${review.timing==='early'?'active':''}">早すぎ</button><button type="button" data-value="late" class="${review.timing==='late'?'active':''}">遅すぎ</button></div></div><label class="actual-row" style="display:flex;align-items:center;gap:9px"><input type="checkbox" data-review-check="tooBroad" ${review.tooBroad?'checked':''}><span><strong>まとめ方が広すぎる / 分かりにくい</strong></span></label><label class="actual-row" style="display:flex;align-items:center;gap:9px"><input type="checkbox" data-review-check="overclaim" ${review.overclaim?'checked':''}><span><strong>記録された事実より強い成果表現がある</strong></span></label></article>`;
}

function renderActual() {
  const d=day();
  if (d.phase==='setup') return `<div class="empty">先に「今日」で既知状態を入力し、候補を封印してください。</div>`;
  return `<section class="section"><div class="section-head"><h2>実際に起きたこと</h2><span>${d.actualLogs.length}件</span></div><button class="primary" id="addActual" type="button">＋ 必要事項を記録</button><div class="stack" style="margin-top:10px">${d.actualLogs.length?d.actualLogs.map(renderActualRow).join(''):'<div class="empty">まだ記録はありません。パートナーから言われたことも、自分で途中で気づいたことも同じ場所へ残します。</div>'}</div>${d.phase==='sealed'?`<article class="card" style="margin-top:10px"><label style="display:flex;align-items:flex-start;gap:9px"><input id="noAdditional" type="checkbox" ${d.explicitNoAdditional?'checked':''}><span><strong>現時点で、ほかに記録すべき必要事項はない</strong><small style="display:block;color:var(--muted);margin-top:4px">空欄を「何も起きなかった」と誤認しないための明示確認です。</small></span></label><button class="secondary" id="confirmAndReveal" type="button" style="margin-top:12px">記録を確定して候補を開く</button></article>`:''}</section>`;
}
function renderActualRow(log) {
  const item=log.responsibilityId?CATALOG.get(log.responsibilityId):null;
  return `<article class="card actual-row" data-actual-id="${esc(log.id)}"><h4>${esc(item?item.label:log.actualLabel)}</h4><p>${esc(SOURCE_LABEL[log.source]||log.source)} ・ ${esc(log.noticedAt.slice(11,16))}</p><div class="meta">${log.partnerPrompted?'<span class="tag warn">先に言われた</span>':''}${log.actualIsHealthSafety?'<span class="tag warn">健康・安全</span>':''}${log.actualIsHardDeadline?'<span class="tag bad">重要締切</span>':''}${log.loopClosed?'<span class="tag good">ループ完了</span>':'<span class="tag">未完了</span>'}</div><div class="mini-actions"><button type="button" data-edit-actual="${esc(log.id)}">編集</button><button type="button" data-delete-actual="${esc(log.id)}">削除</button></div></article>`;
}

function metrics() {
  const d=day();
  if (d.phase!=='revealed') return null;
  const obs=buildObservations();
  const atomic=obs.filter(x=>x.record_scope==='actual_atomic'&&x.actual_required);
  const cards=obs.filter(x=>x.record_scope==='surfaced_card');
  const misses=atomic.filter(x=>!x.engine_surfaced);
  const critical=misses.filter(x=>x.actual_is_health_safety||x.actual_is_hard_deadline);
  const noisy=cards.filter(x=>x.actual_required===false);
  const timing=cards.filter(x=>['early','late'].includes(x.timing));
  const overclaims=cards.filter(x=>x.evidence_overclaim);
  const result={status:(critical.length||overclaims.length)?'BLOCKED':'BASELINE_COMPLETE_WITH_GAPS',atomicRequired:atomic.length,atomicMisses:misses.length,inputGaps:misses.filter(x=>x.input_gap_type==='input_gap').length,ruleGaps:misses.filter(x=>x.input_gap_type==='rule_gap').length,engineMisses:misses.filter(x=>x.input_gap_type==='engine_miss').length,masterGaps:atomic.filter(x=>x.master_gap).length,partnerPrompts:atomic.filter(x=>x.partner_prompted_before_user_notice).length,closeFailures:atomic.filter(x=>!x.loop_closed).length,cards:cards.length,noisyCards:noisy.length,noiseRate:cards.length?noisy.length/cards.length:null,timingErrors:timing.length,tooBroad:cards.filter(x=>x.duplicate_or_too_granular).length,criticalMisses:critical.length,overclaims:overclaims.length};
  return result;
}
function renderExport() {
  const d=day(), m=metrics();
  if (d.phase!=='revealed') return `<div class="stack"><article class="card"><h3>夜の照合後に出力</h3><p>候補を開き、必要性とタイミングを確認すると、atomic責任とcard評価を分けた記録を出力できます。</p></article><button class="ghost" id="exportRaw" type="button">現在のローカル記録をバックアップ</button></div>`;
  return `<section class="section"><div class="section-head"><h2>今日の集計</h2><span>${esc(m.status)}</span></div><div class="metric-grid"><div class="metric"><b>${m.atomicMisses}</b><span>atomic見落とし</span></div><div class="metric"><b>${m.noisyCards}</b><span>不要カード</span></div><div class="metric"><b>${m.partnerPrompts}</b><span>先に言われた必要事項</span></div><div class="metric"><b>${m.closeFailures}</b><span>未完了ループ</span></div><div class="metric"><b>${m.inputGaps}</b><span>入力不足による見落とし</span></div><div class="metric"><b>${m.masterGaps}</b><span>マスターに無い仕事</span></div></div>${m.criticalMisses||m.overclaims?'<p class="notice warn" style="margin-top:10px">Hard gateが発生しています。この状態でactive experimentへ進みません。</p>':'<p class="notice" style="margin-top:10px">これは1日分の基礎集計です。合否判定ではありません。</p>'}<div class="stack" style="margin-top:10px"><button class="primary" id="exportBundle" type="button">実証一式をJSONで保存</button><button class="secondary" id="exportJsonl" type="button">観測行をJSONLで保存</button><button class="ghost" id="copySummary" type="button">集計をコピー</button><button class="danger" id="resetToday" type="button">今日の実証データを削除</button></div></section>`;
}

function openProfile() {
  const c=store.profile.config||{};
  const toggles=[['infant','乳児がいる'],['older_child','上の子がいる'],['daycare','園を利用している'],['two_adult_household','大人2人で家庭運営'],['uses_car','車を使う'],['uses_bicycle_childseat','自転車の幼児座席を使う'],['bottle_used','哺乳瓶を使う'],['expressed_milk_used','搾乳母乳を使う'],['breast_pump_used','搾乳器を使う'],['weaning_started','離乳食を開始'],['local_area_set','地域設定・相談先を確認済み']];
  openModal('家庭条件',`<p class="notice">ここは安定した機能条件だけです。日々変わる体調・在庫・予定は「今日」で入力します。</p>${toggles.map(([id,label])=>`<label class="actual-row" style="display:flex;align-items:center;justify-content:space-between;gap:12px"><span>${esc(label)}</span><input type="checkbox" data-profile="${id}" ${c[id]?'checked':''}></label>`).join('')}<button class="primary" id="saveProfile" type="button" style="margin-top:12px">保存</button>`,()=>document.getElementById('saveProfile').addEventListener('click',()=>{
    const config={};modalBody.querySelectorAll('[data-profile]').forEach(el=>config[el.dataset.profile]=el.checked);
    config.has_child=Boolean(config.infant||config.older_child);config.uses_car_or_bicycle=Boolean(config.uses_car||config.uses_bicycle_childseat);
    const tags=['household'];for(const [key,value] of Object.entries(config))if(value===true)tags.push(key);
    if(config.has_child&&!tags.includes('has_child'))tags.push('has_child');
    store.profile={initialized:true,tags:[...new Set(tags)],config,updatedAt:nowIso()};
    saveStore('profile_saved',{tags:store.profile.tags});closeModal();showToast('家庭条件を保存しました');
  }));
}
function actualForm(existing) {
  const log=existing||{id:uid('actual'),responsibilityId:null,actualLabel:'',source:'self',noticedAt:nowIso(),partnerPrompted:false,actualIsHardDeadline:false,completed:false,loopClosed:false,notes:''};
  const value=log.responsibilityId?`${CATALOG.get(log.responsibilityId)?.label||log.actualLabel} [${log.responsibilityId}]`:log.actualLabel;
  return `<div class="field"><label for="actualSearch">何が必要だった？</label><input id="actualSearch" list="catalogList" value="${esc(value)}" placeholder="項目名を検索。無ければそのまま入力"><datalist id="catalogList">${DATA.catalog.map(x=>`<option value="${esc(x.label)} [${esc(x.id)}]"></option>`).join('')}</datalist><small>マスターに無い内容も、そのまま入力して残せます。</small></div><div class="field"><label for="actualSource">どう気づいた？</label><select id="actualSource">${Object.entries(SOURCE_LABEL).map(([v,l])=>`<option value="${v}" ${log.source===v?'selected':''}>${esc(l)}</option>`).join('')}</select></div><div class="field"><label for="actualTime">気づいた時刻</label><input id="actualTime" type="datetime-local" value="${toLocalInput(log.noticedAt)}"></div><label class="actual-row" style="display:flex;align-items:center;gap:9px"><input id="partnerPrompt" type="checkbox" ${log.partnerPrompted?'checked':''}><span>自分が気づく前に、パートナーから言われた</span></label><label class="actual-row" style="display:flex;align-items:center;gap:9px"><input id="hardDeadline" type="checkbox" ${log.actualIsHardDeadline?'checked':''}><span>重要な締切だった</span></label><label class="actual-row" style="display:flex;align-items:center;gap:9px"><input id="completed" type="checkbox" ${log.completed?'checked':''}><span>着手・実行した</span></label><label class="actual-row" style="display:flex;align-items:center;gap:9px"><input id="loopClosed" type="checkbox" ${log.loopClosed?'checked':''}><span>次回設定・収納・共有まで閉じた</span></label><div class="field"><label for="actualNotes">補足（任意）</label><textarea id="actualNotes">${esc(log.notes)}</textarea></div><button class="primary" id="saveActual" type="button">保存</button>`;
}
function toLocalInput(iso) {
  const d=new Date(iso);const p=n=>String(n).padStart(2,'0');return `${d.getFullYear()}-${p(d.getMonth()+1)}-${p(d.getDate())}T${p(d.getHours())}:${p(d.getMinutes())}`;
}
function saveActual(existingId) {
  const text=document.getElementById('actualSearch').value.trim();
  const match=text.match(/\[([A-Z0-9-]+)\]\s*$/);let responsibilityId=match&&CATALOG.has(match[1])?match[1]:null;
  const actualLabel=responsibilityId?CATALOG.get(responsibilityId).label:text;
  if(!actualLabel){showToast('必要だった内容を入力してください');return;}
  const item=responsibilityId?CATALOG.get(responsibilityId):null;
  const log={id:existingId||uid('actual'),responsibilityId,actualLabel,source:document.getElementById('actualSource').value,noticedAt:new Date(document.getElementById('actualTime').value).toISOString(),partnerPrompted:document.getElementById('partnerPrompt').checked,actualIsHealthSafety:Boolean(item&&(item.type||'').split('/').includes('S')),actualIsHardDeadline:document.getElementById('hardDeadline').checked,completed:document.getElementById('completed').checked,loopClosed:document.getElementById('loopClosed').checked,notes:document.getElementById('actualNotes').value.trim(),createdAt:existingId?(day().actualLogs.find(x=>x.id===existingId)?.createdAt||nowIso()):nowIso(),updatedAt:nowIso()};
  const d=day(),idx=d.actualLogs.findIndex(x=>x.id===log.id);if(idx>=0)d.actualLogs[idx]=log;else d.actualLogs.push(log);
  saveStore(existingId?'actual_updated':'actual_added',{id:log.id,responsibilityId});closeModal();showToast('記録しました');
}
function openActual(id) {
  const existing=id?day().actualLogs.find(x=>x.id===id):null;
  openModal(existing?'必要事項を編集':'必要事項を記録',actualForm(existing),()=>document.getElementById('saveActual').addEventListener('click',()=>saveActual(existing?.id)));
}

function ruleDiagnosis(itemId,state) {
  const entries=RULES_BY_ITEM.get(itemId)||[];
  if(!entries.length)return{ruleCovered:false,inputAvailable:false,type:'rule_gap'};
  let profileEligible=false,conditionTrue=false;const missing=new Set();
  for(const {rule} of entries){const pg=profileGate(rule,state);if(!pg.ok){pg.missing.forEach(x=>missing.add(x));continue;}profileEligible=true;const diag={paths:new Set(),missing:new Set()};const ok=evalCondition(rule.when,state,diag);diag.missing.forEach(x=>missing.add(x));if(ok)conditionTrue=true;}
  if(conditionTrue)return{ruleCovered:true,inputAvailable:true,type:'engine_miss'};
  if(missing.size)return{ruleCovered:true,inputAvailable:false,type:'input_gap',missing:[...missing]};
  if(!profileEligible)return{ruleCovered:true,inputAvailable:false,type:'input_gap'};
  return{ruleCovered:false,inputAvailable:true,type:'rule_gap'};
}
function buildObservations() {
  const d=day(),snap=d.engineSnapshot.payload;const candidateMap=new Map(snap.atomic.map(x=>[x.id,x]));const cardByAtomic=new Map();for(const card of snap.cards)for(const id of card.atomicIds)cardByAtomic.set(id,card);
  const rows=[];
  for(const log of d.actualLogs){const item=log.responsibilityId?CATALOG.get(log.responsibilityId):null;const candidate=log.responsibilityId?candidateMap.get(log.responsibilityId):null;const card=log.responsibilityId?cardByAtomic.get(log.responsibilityId):null;const diag=log.responsibilityId&&!candidate?ruleDiagnosis(log.responsibilityId,d.rawState):null;rows.push({schema_version:2,date:d.date,day_id:d.dayId,snapshot_id:d.engineSnapshot.snapshotId,snapshot_hash:d.engineSnapshot.hash,record_scope:'actual_atomic',responsibility_id:log.responsibilityId,actual_label:log.actualLabel,actual_required:true,actual_priority_class:item?.priority_class||'unknown',actual_is_health_safety:log.actualIsHealthSafety,actual_is_hard_deadline:log.actualIsHardDeadline,source_of_actual_need:log.source,engine_surfaced:Boolean(candidate),surface_card_id:card?.cardId||null,surface_card_label:card?.label||null,engine_layer:candidate?.layer||'not_surfaced',timing:candidate?'right':'not_applicable',engine_candidate_atomic_ids:card?.atomicIds||[],input_available_at_decision_time:candidate?true:(diag?.inputAvailable??false),rule_covered:candidate?true:(diag?.ruleCovered??false),input_gap_type:candidate?'none':(log.responsibilityId?(diag?.type||'engine_miss'):'master_gap'),missing_input_paths:diag?.missing||[],partner_prompted_before_user_notice:log.partnerPrompted,completed:log.completed,loop_closed:log.loopClosed,master_gap:!log.responsibilityId,duplicate_or_too_granular:false,evidence_overclaim:false,noticed_at:log.noticedAt,notes:log.notes});}
  for(const card of snap.cards){const review=d.cardReviews[card.cardId]||{};rows.push({schema_version:2,date:d.date,day_id:d.dayId,snapshot_id:d.engineSnapshot.snapshotId,snapshot_hash:d.engineSnapshot.hash,record_scope:'surfaced_card',responsibility_id:null,actual_label:card.label,actual_required:review.needed==='yes'?true:review.needed==='no'?false:null,actual_priority_class:card.attentionClass||'unknown',actual_is_health_safety:card.containsHealthSafety,actual_is_hard_deadline:false,source_of_actual_need:'engine_snapshot',engine_surfaced:true,surface_card_id:card.cardId,surface_card_label:card.label,engine_layer:card.layer,timing:review.timing||'unreviewed',engine_candidate_atomic_ids:card.atomicIds,input_available_at_decision_time:null,rule_covered:null,input_gap_type:'none',partner_prompted_before_user_notice:false,completed:false,loop_closed:false,master_gap:false,duplicate_or_too_granular:Boolean(review.tooBroad),evidence_overclaim:Boolean(review.overclaim),notes:''});}
  d.observations=rows;localStorage.setItem(STORAGE_KEY,JSON.stringify(store));return rows;
}

async function sealDay() {
  if(!store.profile.initialized){openProfile();return;}
  const d=day();const raw=collectIntake();const payload=derive(raw);const canonical=JSON.stringify(payload);const hash=await sha256(canonical);d.engineSnapshot={snapshotId:uid('snapshot'),generatedAt:payload.generatedAt,hash,payload};d.phase='sealed';d.actualLogConfirmedAt=null;d.revealedAt=null;d.cardReviews={};d.observations=[];saveStore('engine_snapshot_sealed',{snapshotId:d.engineSnapshot.snapshotId,hash});showToast('候補を封印しました');
}
function confirmReveal() {
  const d=day();if(!d.actualLogs.length&&!d.explicitNoAdditional){showToast('必要事項を記録するか、「ほかにない」を確認してください');return;}
  d.actualLogConfirmedAt=nowIso();d.phase='revealed';d.revealedAt=nowIso();buildObservations();saveStore('engine_snapshot_revealed',{snapshotId:d.engineSnapshot.snapshotId,actualLogCount:d.actualLogs.length});activeView='today';showToast('候補を開きました');
}
function download(name,text,type='application/json') {const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([text],{type}));a.download=name;document.body.appendChild(a);a.click();setTimeout(()=>{URL.revokeObjectURL(a.href);a.remove();},500);}
function exportBundle() {const d=day();const bundle={schema_version:2,exported_at:nowIso(),build:DATA.build,profile:store.profile,day:{...d,observations:buildObservations()},audit:store.audit.filter(x=>x.at.slice(0,10)===d.date)};download(`kajitori-shadow-v2-${d.date}.json`,JSON.stringify(bundle,null,2));}
function exportJsonl() {const d=day();const rows=buildObservations();download(`kajitori-shadow-v2-${d.date}.jsonl`,rows.map(x=>JSON.stringify(x)).join('\n')+'\n','application/x-ndjson');}
function exportRaw() {download(`kajitori-shadow-v2-backup-${localDate()}.json`,JSON.stringify(store,null,2));}

function bind() {
  document.getElementById('settingsBtn').onclick=openProfile;
  document.querySelectorAll('.bottom-nav button').forEach(btn=>btn.onclick=()=>{activeView=btn.dataset.view;render();});
  document.getElementById('openProfile')?.addEventListener('click',openProfile);
  document.getElementById('sealBtn')?.addEventListener('click',sealDay);
  document.getElementById('goActual')?.addEventListener('click',()=>{activeView='actual';render();});
  document.getElementById('revealStart')?.addEventListener('click',()=>{activeView='actual';render();});
  document.getElementById('addActual')?.addEventListener('click',()=>openActual());
  document.querySelectorAll('[data-edit-actual]').forEach(btn=>btn.onclick=()=>openActual(btn.dataset.editActual));
  document.querySelectorAll('[data-delete-actual]').forEach(btn=>btn.onclick=()=>{const d=day();const id=btn.dataset.deleteActual;const old=d.actualLogs.find(x=>x.id===id);if(!confirm('この記録を削除しますか？'))return;d.actualLogs=d.actualLogs.filter(x=>x.id!==id);saveStore('actual_deleted',{id,old});});
  document.getElementById('noAdditional')?.addEventListener('change',e=>{day().explicitNoAdditional=e.target.checked;saveStore('explicit_no_additional_changed',{value:e.target.checked});});
  document.getElementById('confirmAndReveal')?.addEventListener('click',confirmReveal);
  document.querySelectorAll('[data-card-id]').forEach(cardEl=>{const cardId=cardEl.dataset.cardId;cardEl.querySelectorAll('[data-review]').forEach(group=>group.querySelectorAll('button').forEach(btn=>btn.onclick=()=>{const d=day();d.cardReviews[cardId] ||= {};d.cardReviews[cardId][group.dataset.review]=btn.dataset.value;saveStore('card_review_changed',{cardId,field:group.dataset.review,value:btn.dataset.value});}));cardEl.querySelectorAll('[data-review-check]').forEach(el=>el.onchange=()=>{const d=day();d.cardReviews[cardId] ||= {};d.cardReviews[cardId][el.dataset.reviewCheck]=el.checked;saveStore('card_review_changed',{cardId,field:el.dataset.reviewCheck,value:el.checked});});});
  document.getElementById('exportBundle')?.addEventListener('click',exportBundle);
  document.getElementById('exportJsonl')?.addEventListener('click',exportJsonl);
  document.getElementById('exportRaw')?.addEventListener('click',exportRaw);
  document.getElementById('copySummary')?.addEventListener('click',async()=>{await navigator.clipboard.writeText(JSON.stringify(metrics(),null,2));showToast('集計をコピーしました');});
  document.getElementById('resetToday')?.addEventListener('click',()=>{if(!confirm('今日の実証データを削除しますか？監査履歴にも削除を残します。'))return;const key=localDate(),old=store.days[key];delete store.days[key];store.audit.push({id:uid('audit'),at:nowIso(),action:'day_deleted',detail:{dayId:old?.dayId,date:key}});localStorage.setItem(STORAGE_KEY,JSON.stringify(store));activeView='today';render();});
  bindTri();
}
function render() {
  const d=day();document.getElementById('headerStatus').textContent=`${d.date} ・ ${d.phase==='setup'?'入力前':d.phase==='sealed'?'封印中':'照合中'} ・ build ${DATA.build.id.slice(0,10)}`;
  document.querySelectorAll('.bottom-nav button').forEach(btn=>btn.classList.toggle('active',btn.dataset.view===activeView));
  main.innerHTML=activeView==='today'?renderToday():activeView==='actual'?renderActual():renderExport();bind();
}

document.getElementById('modalClose').onclick=closeModal;
modal.addEventListener('click',e=>{if(e.target===modal)closeModal();});
render();
})();
