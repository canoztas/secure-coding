'use strict';

const LABS = [
  {id:'search',name:'Arama',title:'Fatura arama',description:'Satın alma kayıtlarında küçük bir arama.',screen:'Faturalarım',task:'Arama sınırlarını dene',goal:'Alice olarak, arama kutusundan sana ait olmayan bir faturayı getir.',rule:'Arama sonucu yalnız kullanıcının okuma izni olan faturaları içermeli.',hint:'Arama metni yalnız veri olarak mı kullanılıyor, yoksa sorgunun yapısını değiştirebiliyor mu?'},
  {id:'object',name:'Fatura erişimi',title:'Kimin faturası?',description:'Aynı şirkette olmak her kayda erişim izni vermez.',screen:'Fatura ayrıntısı',task:'102 numaralı kayda bak',goal:'Alice olarak Bob’un 102 numaralı faturasını açmayı dene. Ardından düzeltilmiş sürümde aynı isteği gönder.',rule:'Üye yalnız kendi faturasını okuyabilir. Muhasebeci kendi şirketinin faturalarını görebilir.',hint:'Liste ekranındaki filtreyle ayrıntı adresindeki izin kontrolü aynı şey mi?'},
  {id:'fields',name:'Alan izinleri',title:'Bir nottan fazlası',description:'Faturanın teslimat notunu güncelle.',screen:'101 numaralı faturayı düzenle',task:'Üye faturayı onaylayabilir mi?',goal:'Alice’in not güncelleme isteğini değiştirerek 101 numaralı faturayı approved durumuna getir.',rule:'Üye notu değiştirebilir; fatura onayı ayrı bir yetki gerektirir.',hint:'İstekte, formda görünmeyen bir alan gönderirsen sunucu onu da kabul ediyor mu?'},
  {id:'notes',name:'Teslimat notu',title:'Not mu, kod mu?',description:'Kaydedilen notun teslimat ekranında nasıl göründüğüne bak.',screen:'Teslimat notum',task:'Tarayıcıda kod çalışmasını göster',goal:'Kaydedilen not üzerinden JavaScript çalıştır. Kanıt için alert("merhaba") çağrısını kullanabilirsin; mesaj önizlemede gösterilir.',rule:'Kullanıcı notu, tarayıcıda çalıştırılacak kod olarak yorumlanmamalı.',hint:'Kaydedilen metin HTML olarak mı ekleniyor? Bir HTML olay işleyicisi denemek neyi gösterir?'},
  {id:'price',name:'Ürün fiyatı',title:'Fiyatı kim belirliyor?',description:'Ofis için bir ürün sipariş et.',screen:'Ofis malzemeleri',task:'Katalogdan ucuza sipariş ver',goal:'Sipariş isteğindeki birim fiyatı değiştir. Sunucunun daha düşük tutarla sipariş oluşturup oluşturmadığını gözle.',rule:'Fiyat katalogdan, adet doğrulanmış kullanıcı isteğinden gelmeli.',hint:'Ekranda salt okunur görünen bir tutar, HTTP isteğinde de değiştirilemez mi?'},
  {id:'coupon',name:'İndirim kuponu',title:'Bir kereye mahsus',description:'MERHABA20 kuponuyla %20 indirim.',screen:'Sepet özeti',task:'Aynı kuponu yeniden kullan',goal:'Tek kullanımlık kuponla sepete birden fazla indirim uygula.',rule:'MERHABA20 her kullanıcı için yalnız bir kez kullanılabilir.',hint:'İlk başarılı isteği bir kez daha gönder. Arayüzdeki durumun sunucuda karşılığı var mı?'},
  {id:'workflow',name:'Ödeme akışı',title:'Bir adımı atlarsak?',description:'501 numaralı siparişin ödeme ve teslimat akışı.',screen:'Sipariş 501',task:'Ödemeden teslimat onayı al',goal:'Alice olarak ödeme yapmadan siparişi teslimata onayla. Sonra düzeltilmiş sürümde aynı sırayı dene.',rule:'Teslimat onayı, sunucuda doğrulanmış bir ödemeden sonra verilebilir.',hint:'Ödeme düğmesine basmadan onay adresine doğrudan bir istek gönderebilir misin?'},
  {id:'jwt',name:'JWT ile kimlik',title:'Token’da kim yazıyor?',description:'Token’ı çöz, alanlarını değiştir ve aynı token’ı iki sürümde dene.',screen:'JWT çalışma alanı',task:'Token ile başka kullanıcı ol',goal:'Alice’in token’ında sub alanını bob yap veya role alanını accountant olarak değiştir. İmza üretmeden Bob’un faturasını okumayı dene.',rule:'Token içeriği okunabilir; içindeki kimliğe ve role güvenmeden önce imza, süre, üretici ve hedef doğrulanmalı.',hint:'Payload’u değiştirmek imzayı yenilemez. Kullanıcı alanları: alice / bob; roller: member / accountant. jwt_tool çıktısını da token alanına yapıştırabilirsin.'}
];
const $ = selector => document.querySelector(selector);
const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const money = cents => new Intl.NumberFormat('tr-TR',{style:'currency',currency:'TRY',maximumFractionDigits:2}).format(cents / 100);
const statusNames = {draft:'Taslak',issued:'Kesinleşmiş',approved:'Onaylı',unpaid:'Ödenmedi',paid:'Ödendi',awaiting_payment:'Ödeme bekliyor',ready:'Onaya hazır',confirmed:'Teslimat onaylandı'};
const status = value => `<span class="status ${esc(value)}">${esc(statusNames[value] || value)}</span>`;
const state = {lab:LABS.find(x=>x.id === location.hash.slice(1)) || LABS[0],mode:'vulnerable',boot:null,overview:null,detail:null,busy:false,seenXss:new Set(),jwtToken:'',jwtDraft:'',jwtResult:null,jwtInitialized:false};
const codeCache=new Map();
let currentCode=null;
let toastTimer;

function toast(message) {
  $('#toast').textContent=message; $('#toast').hidden=false;
  clearTimeout(toastTimer);toastTimer=setTimeout(()=>{$('#toast').hidden=true;},4200);
}
function showError(error) {$('#global-error').textContent=error.message || String(error);$('#global-error').hidden=false;}
async function jsonFetch(path, method='GET', payload, authorization='') {
  const options={method,credentials:'same-origin',headers:{'Accept':'application/json'}};
  if(authorization.trim())options.headers.Authorization=authorization.trim();
  if (method!=='GET') {options.headers['Content-Type']='application/json';options.body=JSON.stringify(payload ?? {});}
  const response=await fetch(path,options);
  const data=await response.json();
  return {response,data};
}
async function bootstrap() {
  const {response,data}=await jsonFetch('/api/bootstrap');
  if(!response.ok)throw new Error(data.message);
  state.boot=data;
  $('#actor').innerHTML=data.actors.map(x=>`<option value="${esc(x.id)}">${esc(x.name)} · Şirket ${esc(x.company)} · ${esc(x.role_label)}</option>`).join('');
  $('#actor').value=data.actor.id;renderNav();
}
async function loadOverview() {
  const {response,data}=await jsonFetch(`/api/${state.mode}/overview`);
  if(!response.ok)throw new Error(data.message);
  await loadCode();
  if(state.lab.id==='jwt'&&!state.jwtInitialized)await issueJwtToken();
  state.overview=data;state.boot.progress=data.progress;renderNav();
}
function highlightPython(line) {
  const tokens=/(#[^\n]*|(?:\b[frbu]{1,2})?(?:"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*')|\b(?:if|else|elif|return|raise|def|and|or|not|in|for|is|None|True|False)\b|\b\d+\b)/gi;
  let result='',last=0;
  for(const match of line.matchAll(tokens)){
    result+=esc(line.slice(last,match.index));
    const token=match[0],type=token.startsWith('#')?'comment':/^[frbu]*["']/i.test(token)?'string':/^\d/.test(token)?'number':'keyword';
    result+=`<span class="py-${type}">${esc(token)}</span>`;last=match.index+token.length;
  }
  return result+esc(line.slice(last));
}
async function loadCode() {
  const lab=state.lab.id,mode=state.mode,key=`${lab}:${mode}`;
  if(!codeCache.has(key)){
    const {response,data}=await jsonFetch(`/api/${mode}/code/${lab}`);
    if(!response.ok)throw new Error(data.message);
    codeCache.set(key,data);
  }
  if(key!==`${state.lab.id}:${state.mode}`)return;
  const view=codeCache.get(key);currentCode=view;
  $('#code-version').textContent=`${mode==='fixed'?'Düzeltilmiş sürüm':'Zafiyetli sürüm'} · Python`;
  $('#code-question').textContent=view.question;
  $('#code-context').textContent=`mode = "${mode}" · Vurgular, bu sürüme ait koşul dallarını gösterir.`;
  $('#code-blocks').innerHTML=view.blocks.map(block=>{
    const focus=new Set(block.focus_lines);
    const rows=block.code.split('\n').map((line,i)=>`<span class="source-line${focus.has(block.start_line+i)?' source-focus':''}"><span class="source-number" aria-hidden="true">${block.start_line+i}</span><span class="source-text">${highlightPython(line)||' '}</span></span>`).join('');
    return `<div class="source-block"><div class="source-file">${esc(block.file)} · ${block.start_line}–${block.end_line}</div><pre tabindex="0" aria-label="${esc(block.file)} kaynak kodu"><code>${rows}</code></pre></div>`;
  }).join('');
}
function renderNav() {
  const progress=state.boot?.progress || {};
  $('#progress-count').textContent=`${Object.keys(progress).length} / ${LABS.length}`;
  $('#labs').innerHTML=LABS.map((lab,i)=>`<button type="button" class="lab-button ${state.lab.id===lab.id?'active':''} ${progress[lab.id]?'complete':''}" data-lab="${lab.id}" ${state.lab.id===lab.id?'aria-current="page"':''}><span class="number">${String(i+1).padStart(2,'0')}</span><span>${lab.name}</span>${progress[lab.id]?'<span class="done" aria-label="Kanıt gözlendi">✓</span>':''}</button>`).join('');
  renderEvidence();
}
function renderEvidence() {
  const evidence=state.boot?.progress[state.lab.id];
  const box=$('#evidence');box.className=`evidence${evidence?' complete':''}`;
  if(evidence){box.innerHTML=`<strong>${state.mode==='fixed'?'Zafiyetli sürümde gözlenen etki':'Etki gözlendi'}</strong><span>${esc(evidence.evidence)}</span>`;}
  else{box.textContent='Henüz etki gözlenmedi. Normal bir işlemle başla; sonra isteği değiştir.';}
}
function renderHeading() {
  const lab=state.lab,index=LABS.indexOf(lab)+1;
  $('#lab-number').textContent=`ÇALIŞMA ${String(index).padStart(2,'0')} / ${LABS.length}`;
  $('#lab-title').textContent=lab.title;$('#lab-description').textContent=lab.description;
  $('#screen-title').textContent=lab.screen;$('#task-title').textContent=lab.task;$('#task-goal').textContent=lab.goal;$('#task-rule').textContent=lab.rule;
  $('#hint').textContent=lab.hint;$('#hint').hidden=true;$('#hint-toggle').setAttribute('aria-expanded','false');
  $('#company-label').textContent=`${state.boot.actor.name} · Şirket ${state.boot.actor.company}`;
  $('#mode-label').textContent=state.mode==='fixed'?'Düzeltilmiş sürüm':'Zafiyetli sürüm';
  $('#mode-label').classList.toggle('fixed',state.mode==='fixed');
  document.querySelectorAll('[data-mode]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.mode===state.mode)));
  $('#auth-field').hidden=state.lab.id!=='jwt';
  $('#path-help').textContent=state.lab.id==='jwt'?'Authorization başlığındaki token sunucuya gönderilir.':'Tutarlar API’de tam sayı kuruş olarak taşınır.';
  renderEvidence();
}
function invoicesTable(invoices,interactive=true) {
  if(!invoices.length)return '<p class="empty">Bu aramada fatura bulunamadı.</p>';
  return `<div class="table-scroll"><table><thead><tr><th>FATURA</th><th>AÇIKLAMA</th><th>SAHİP</th><th>TUTAR</th><th>DURUM</th></tr></thead><tbody>${invoices.map(x=>`<tr><td>${interactive?`<button type="button" class="invoice-link" data-invoice="${x.id}">#${x.id}</button>`:`<span>#${x.id}</span>`}</td><td>${esc(x.title)}</td><td>${esc(x.owner_id)} · ${esc(x.company)}</td><td>${money(x.amount_cents)}</td><td>${status(x.status)}</td></tr>`).join('')}</tbody></table></div>`;
}
function invoiceDetails(invoice) {
  if(!invoice)return '<p class="empty">Bir fatura numarası girip ayrıntısını aç.</p>';
  return `<div class="panel-body"><h3>#${invoice.id} · ${esc(invoice.title)}</h3><dl class="details"><div><dt>Sahibi</dt><dd>${esc(invoice.owner_id)}</dd></div><div><dt>Şirket</dt><dd>${esc(invoice.company)}</dd></div><div><dt>Tutar</dt><dd>${money(invoice.amount_cents)}</dd></div><div><dt>Durum</dt><dd>${status(invoice.status)}</dd></div></dl><p class="record-note">${esc(invoice.note)}</p></div>`;
}
function renderWorkspace() {
  const data=state.overview,root=$('#workspace'),lab=state.lab.id;
  if(lab==='search') {
    root.innerHTML=`<div class="panel-body"><form id="search-form" class="inline-form"><label for="search-query">Fatura açıklaması<input id="search-query" placeholder="Örneğin: ofis" autocomplete="off"></label><button type="submit">Ara</button></form></div><div id="search-results">${invoicesTable(data.invoices)}</div>`;
  } else if(lab==='object') {
    const selected=state.detail || data.invoices[0];
    root.innerHTML=`<div class="panel-body"><form id="invoice-form" class="inline-form"><label for="invoice-id">Fatura numarası<input id="invoice-id" inputmode="numeric" type="number" min="1" value="${selected?.id || 101}"></label><button type="submit">Faturayı aç</button></form></div><div id="invoice-details">${invoiceDetails(selected)}</div>`;
  } else if(lab==='fields') {
    const invoice=data.invoices.find(x=>x.id===101);
    root.innerHTML=invoice?`<div class="panel-body"><h3>${esc(invoice.title)}</h3><dl class="details"><div><dt>Sahibi</dt><dd>${esc(invoice.owner_id)}</dd></div><div><dt>Durum</dt><dd>${status(invoice.status)}</dd></div></dl><form id="edit-form"><label class="full-label" for="invoice-note">Teslimat notu</label><textarea id="invoice-note" class="full-input" rows="3" maxlength="1000">${esc(invoice.note)}</textarea><button class="primary" type="submit">Notu kaydet</button></form></div>`:'<p class="empty">101 numaralı fatura Alice’e ait. Bu çalışma için Alice hesabını seç.</p>';
  } else if(lab==='notes') {
    root.innerHTML=`<div class="panel-body"><form id="note-form"><label class="full-label" for="delivery-note">Teslimat ekibine not</label><textarea id="delivery-note" class="note-editor" maxlength="2000">${esc(data.note)}</textarea><div class="button-row section-space"><button class="primary" type="submit">Notu kaydet</button></div></form><p class="preview-heading">Kaydedilen notun önizlemesi</p><iframe id="note-frame" class="note-preview" title="Kaydedilen teslimat notu" sandbox="allow-scripts" src="/preview/${state.mode}/notes"></iframe></div>`;
  } else if(lab==='price') {
    root.innerHTML=`<div class="product-list">${state.boot.products.map(p=>`<div class="product"><div><h3>${esc(p.name)}</h3><p>${money(p.price_cents)} / adet</p></div><button type="button" data-product="${p.id}">Sipariş ver</button></div>`).join('')}</div><div class="orders-list"><h3>Son siparişlerim</h3>${data.orders.length?data.orders.slice(-4).reverse().map(o=>`<div class="order-row"><span>#${o.id} · ${esc(state.boot.products.find(p=>p.id===o.product_id)?.name)} × ${o.quantity}</span><strong>${money(o.total_cents)}</strong></div>`).join(''):'<p class="muted">Henüz sipariş yok.</p>'}</div>`;
  } else if(lab==='coupon') {
    root.innerHTML=`<div class="panel-body"><p class="amount-caption">Sepet tutarı</p><p class="large-amount">${money(data.coupon.total_cents)}</p><p class="subtle">Başlangıç tutarı: ${money(100000)}</p><div class="section-space"><span class="coupon-code">MERHABA20</span><p class="help-line">%20 indirim · Kullanıcı başına bir kez.</p><button id="apply-coupon" type="button" class="primary" ${data.coupon.used?'disabled':''}>${data.coupon.used?'Kupon uygulandı':'Kuponu uygula'}</button></div></div>`;
  } else if(lab==='workflow') {
    const order=data.delivery;
    root.innerHTML=order?`<div class="panel-body"><p class="amount-caption">Sipariş toplamı</p><p class="large-amount">${money(order.amount_cents)}</p><dl class="details"><div><dt>Ödeme</dt><dd>${status(order.payment_status)}</dd></div><div><dt>Sipariş</dt><dd>${status(order.status)}</dd></div></dl><div class="flow-steps"><div class="flow-step done">1 · Sipariş</div><div class="flow-step ${order.payment_status==='paid'?'done':''}">2 · Ödeme</div><div class="flow-step ${order.status==='confirmed'?(order.payment_status==='paid'?'done':'problem'):''}">3 · Teslimat onayı</div></div><div class="button-row"><button type="button" class="primary" id="pay-order" ${order.payment_status==='paid'||order.status==='confirmed'?'disabled':''}>Deneme ödemesi yap</button><button type="button" id="confirm-order" ${order.payment_status!=='paid'||order.status==='confirmed'?'disabled':''}>Teslimatı onayla</button></div><p class="subtle">Deneme ödemesi gerçek bir para hareketi oluşturmaz.</p></div>`:'<p class="empty">501 numaralı sipariş Alice’e ait. Bu çalışma için Alice hesabını seç.</p>';
  } else if(lab==='jwt') {
    root.innerHTML=renderJwtWorkspace();
    $('#authorization').value=state.jwtToken?`Bearer ${state.jwtToken}`:'';
  }
}
function defaults() {
  const prefix=`/api/${state.mode}`;
  const requests={search:['GET',`${prefix}/invoices/search?q=ofis`,null],object:['GET',`${prefix}/invoices/101`,null],fields:['PATCH',`${prefix}/invoices/101`,{note:'Teslimat sabah yapılsın.'}],notes:['POST',`${prefix}/notes`,{note:'Teslimatı mesai saatlerinde yapınız.'}],price:['POST',`${prefix}/orders`,{product_id:'hub',quantity:1,unit_price_cents:90000}],coupon:['POST',`${prefix}/coupons/apply`,{code:'MERHABA20'}],workflow:['POST',`${prefix}/orders/501/confirm`,{}]};
  if(state.lab.id==='jwt'){
    setRequest('GET',`${prefix}/jwt/invoices`,null);
    $('#authorization').value=state.jwtToken?`Bearer ${state.jwtToken}`:'';
  } else setRequest(...requests[state.lab.id]);
}
function setRequest(method,path,body) {$('#method').value=method;$('#path').value=path;$('#body').value=body===null?'':JSON.stringify(body,null,2);}
function showResponse(response,data) {
  const version=response.url.includes('/api/fixed/')?'Düzeltilmiş':'Zafiyetli';
  $('#response-status').textContent=`HTTP ${response.status} · ${version}`;$('#response-status').classList.toggle('bad',!response.ok);
  $('#response').textContent=JSON.stringify(data,null,2);
}
async function executeRequest(method,path,payload,options={}) {
  if(state.busy)return null;
  const prefix=`/api/${state.mode}/`;
  if(!path.startsWith(prefix)||path.includes('://'))throw new Error('İstek yolu seçili sürümün /api/ adresiyle başlamalı.');
  state.busy=true;$('#send-request').disabled=true;$('#global-error').hidden=true;
  setRequest(method,path,payload);
  try {
    const {response,data}=await jsonFetch(path,method,payload,state.lab.id==='jwt'?$('#authorization').value:'');showResponse(response,data);
    if(state.lab.id==='jwt' && path.endsWith('/jwt/invoices'))state.jwtResult={ok:response.ok,status:response.status,data,mode:state.mode};
    if(response.ok && state.lab.id==='object' && data.invoice)state.detail=data.invoice;
    await loadOverview();
    if(options.search && response.ok && Array.isArray(data.invoices))$('#search-results').innerHTML=invoicesTable(data.invoices);
    else if(options.detail && response.ok && data.invoice)$('#invoice-details').innerHTML=invoiceDetails(data.invoice);
    else if(!options.search && !options.detail)renderWorkspace();
    if(response.ok && ['PATCH','POST'].includes(method))toast('İşlem tamamlandı. Sunucu yanıtını inceleyebilirsin.');
    return {response,data};
  } finally {state.busy=false;$('#send-request').disabled=false;}
}
async function chooseLab(id) {
  const lab=LABS.find(x=>x.id===id);if(!lab||state.busy)return;
  state.lab=lab;state.detail=null;history.replaceState(null,'',`#${id}`);
  $('#global-error').hidden=true;await loadOverview();renderNav();renderHeading();renderWorkspace();defaults();
  $('#response-status').textContent='Henüz istek yok';$('#response-status').classList.remove('bad');$('#response').textContent='Bir işlem yap veya örnek isteği gönder.';
}
async function guarded(fn) {try {await fn();}catch(error){showError(error);}}

$('#labs').addEventListener('click',event=>{const b=event.target.closest('[data-lab]');if(b)guarded(()=>chooseLab(b.dataset.lab));});
document.querySelectorAll('[data-mode]').forEach(button=>button.addEventListener('click',()=>guarded(async()=>{
  if(state.busy||state.mode===button.dataset.mode)return;
  state.mode=button.dataset.mode;state.detail=null;state.jwtResult=null;
  $('#path').value=$('#path').value.replace(/^\/api\/(vulnerable|fixed)\//,`/api/${state.mode}/`);
  await loadOverview();renderHeading();renderWorkspace();$('#global-error').hidden=true;
})));
$('#actor').addEventListener('change',()=>guarded(async()=>{
  if(state.busy){$('#actor').value=state.boot.actor.id;return;}
  const {response,data}=await jsonFetch('/api/actor','POST',{actor:$('#actor').value});if(!response.ok)throw new Error(data.message);
  state.boot.actor=data.actor;state.detail=null;state.jwtToken='';state.jwtDraft='';state.jwtResult=null;state.jwtInitialized=false;await loadOverview();renderHeading();renderWorkspace();
}));
$('#hint-toggle').addEventListener('click',()=>{const hidden=!$('#hint').hidden;$('#hint').hidden=hidden;$('#hint-toggle').setAttribute('aria-expanded',String(!hidden));});
$('#request-default').addEventListener('click',defaults);
$('#copy-code').addEventListener('click',()=>guarded(async()=>{
  if(!currentCode)return;
  const text=currentCode.blocks.map(block=>block.code).join('\n\n');
  try{await navigator.clipboard.writeText(text);toast('Kod kopyalandı.');}
  catch{throw new Error('Kopyalama izni alınamadı. Kod alanından seçip kopyalayabilirsin.');}
}));
$('#request-form').addEventListener('submit',event=>{event.preventDefault();guarded(async()=>{
  const method=$('#method').value,path=$('#path').value.trim();let data=null;
  if(method!=='GET'){try{data=JSON.parse($('#body').value||'{}');}catch{throw new Error('JSON gövdesini kontrol et: alan adları çift tırnak içinde olmalı.');}}
  await executeRequest(method,path,data,{search:state.lab.id==='search',detail:state.lab.id==='object'});
});});
$('#workspace').addEventListener('submit',event=>{event.preventDefault();guarded(async()=>{
  const prefix=`/api/${state.mode}`;
  if(event.target.id==='search-form')await executeRequest('GET',`${prefix}/invoices/search?${new URLSearchParams({q:$('#search-query').value})}`,null,{search:true});
  if(event.target.id==='invoice-form')await executeRequest('GET',`${prefix}/invoices/${encodeURIComponent($('#invoice-id').value)}`,null,{detail:true});
  if(event.target.id==='edit-form')await executeRequest('PATCH',`${prefix}/invoices/101`,{note:$('#invoice-note').value});
  if(event.target.id==='note-form')await executeRequest('POST',`${prefix}/notes`,{note:$('#delivery-note').value});
});});
$('#workspace').addEventListener('click',event=>guarded(async()=>{
  const prefix=`/api/${state.mode}`,invoice=event.target.closest('[data-invoice]'),product=event.target.closest('[data-product]');
  if(invoice){
    const result=await executeRequest('GET',`${prefix}/invoices/${invoice.dataset.invoice}`,null,{detail:state.lab.id==='object'});
    if(result?.response.ok && state.lab.id==='search'){
      const extra=document.createElement('div');extra.className='section-space';extra.innerHTML=invoiceDetails(result.data.invoice);$('#search-results').append(extra);
    }
  }
  if(product){const p=state.boot.products.find(x=>x.id===product.dataset.product);await executeRequest('POST',`${prefix}/orders`,{product_id:p.id,quantity:1,unit_price_cents:p.price_cents});}
  if(event.target.id==='apply-coupon')await executeRequest('POST',`${prefix}/coupons/apply`,{code:'MERHABA20'});
  if(event.target.id==='pay-order')await executeRequest('POST',`${prefix}/orders/501/pay`,{});
  if(event.target.id==='confirm-order')await executeRequest('POST',`${prefix}/orders/501/confirm`,{});
}));
window.addEventListener('message',event=>guarded(async()=>{
  const frame=$('#note-frame'),data=event.data;
  if(!frame||event.source!==frame.contentWindow||data?.type!=='lab:xss'||typeof data.nonce!=='string'||state.mode!=='vulnerable')return;
  const key=`${data.nonce}:${state.boot.actor.id}`;if(state.seenXss.has(key))return;
  state.seenXss.add(key);
  const result=await jsonFetch('/api/vulnerable/notes/proof','POST',{nonce:data.nonce});
  if(result.response.ok){await bootstrap();renderEvidence();toast('Not içindeki kod tarayıcıda çalıştı. Etki kaydedildi.');}
}));
$('#reset').addEventListener('click',()=>{if(!state.busy)$('#reset-dialog').showModal();});
$('#reset-dialog').addEventListener('close',()=>guarded(async()=>{
  if($('#reset-dialog').returnValue!=='reset')return;
  const {response,data}=await jsonFetch('/api/reset','POST',{});if(!response.ok)throw new Error(data.message);
  state.seenXss.clear();state.detail=null;state.jwtToken='';state.jwtDraft='';state.jwtResult=null;state.jwtInitialized=false;await bootstrap();await loadOverview();renderHeading();renderWorkspace();defaults();toast(data.message);
}));
setupJwtTools();
guarded(async()=>{await bootstrap();await chooseLab(state.lab.id);});
