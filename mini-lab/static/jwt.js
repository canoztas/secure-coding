'use strict';

function parseLabJwt(raw) {
  const token=raw.trim().replace(/^Bearer\s+/i,''),parts=token.split('.');
  if(parts.length!==3||!parts[0]||!parts[1]||token.length>4096)throw new Error('Token üç parçadan oluşmalı: header.payload.signature.');
  const decode=part=>{
    const text=atob(part.replace(/-/g,'+').replace(/_/g,'/').padEnd(Math.ceil(part.length/4)*4,'='));
    return JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(Uint8Array.from(text,c=>c.charCodeAt(0))));
  };
  try{
    const header=decode(parts[0]),payload=decode(parts[1]);
    if(!header||Array.isArray(header)||typeof header!=='object'||!payload||Array.isArray(payload)||typeof payload!=='object')throw new Error();
    return {token,parts,header,payload};
  }catch{throw new Error('Header veya payload okunamadı. Base64url ve JSON biçimini kontrol et.');}
}
async function issueJwtToken() {
  const {response,data}=await jsonFetch(`/api/${state.mode}/jwt/issue`,'POST',{});
  if(!response.ok)throw new Error(data.message);
  const parsed=parseLabJwt(data.token);
  state.jwtToken=parsed.token;state.jwtDraft=JSON.stringify(parsed.payload,null,2);state.jwtResult=null;state.jwtInitialized=true;
}
function renderJwtWorkspace() {
  let header='Token’ı çözerek header bilgisini görebilirsin.';
  try{header=JSON.stringify(parseLabJwt(state.jwtToken).header);}catch{}
  const result=state.jwtResult;
  let output='<p class="empty">Token’ı gönderince sunucunun kabul ettiği kimlik ve faturalar burada görünür.</p>';
  if(result?.ok){
    const identity=result.data.identity;
    output=`<div class="jwt-identity"><span>Sunucunun kabul ettiği kimlik</span><strong>${esc(identity.name)} · ${esc(identity.role)} · Şirket ${esc(identity.company)}</strong></div>${invoicesTable(result.data.invoices,false)}`;
  }else if(result){output=`<div class="panel-body"><div class="notice error"><strong>HTTP ${result.status} · Token reddedildi</strong><p>${esc(result.data.message)}</p></div></div>`;}
  return `<div class="panel-body jwt-editor"><div class="jwt-topline"><p>Token’daki bilgiyi okumak, doğrulamak anlamına gelmez.</p><button type="button" class="text-button" id="jwt-issue">Yeni ders token’ı al</button></div><label class="full-label" for="jwt-token">Token · jwt_tool çıktısını da buraya yapıştırabilirsin</label><textarea id="jwt-token" rows="4" maxlength="4096" spellcheck="false">${esc(state.jwtToken)}</textarea><div class="button-row jwt-small-actions"><button type="button" id="jwt-decode">Token’ı çöz</button><button type="button" class="text-button" id="jwt-copy">Token’ı kopyala</button></div><p class="jwt-header">Header <code>${esc(header)}</code></p><label class="full-label" for="jwt-payload">Payload · sub, role veya company alanını değiştir</label><textarea id="jwt-payload" rows="9" maxlength="4096" spellcheck="false">${esc(state.jwtDraft)}</textarea><div class="button-row section-space"><button type="button" id="jwt-apply">Payload’u token’a yaz</button><button type="button" class="primary" id="jwt-send">Faturaları bu token’la getir</button></div><p class="subtle">Payload’u yazarken mevcut imza aynen korunur; yeni imza üretilmez. Aynı token’ı düzeltilmiş sürümde de dene.</p></div><div id="jwt-result">${output}</div>`;
}
function setupJwtTools() {
  $('#workspace').addEventListener('input',event=>{
    if(event.target.id==='jwt-payload')state.jwtDraft=event.target.value;
    if(event.target.id==='jwt-token'){
      state.jwtToken=event.target.value.trim().replace(/^Bearer\s+/i,'');
      $('#authorization').value=state.jwtToken?`Bearer ${state.jwtToken}`:'';
    }
  });
  $('#authorization').addEventListener('input',()=>{
    if(state.lab.id!=='jwt')return;
    state.jwtToken=$('#authorization').value.trim().replace(/^Bearer\s+/i,'');
    if($('#jwt-token'))$('#jwt-token').value=state.jwtToken;
  });
  $('#workspace').addEventListener('click',event=>guarded(async()=>{
    if(state.busy)return;
    const id=event.target.id;
    if(id==='jwt-issue'){
      await issueJwtToken();renderWorkspace();defaults();toast('Seçili ders hesabı için yeni imzalı token alındı.');
    }
    if(id==='jwt-decode'){
      const parsed=parseLabJwt($('#jwt-token').value);
      state.jwtToken=parsed.token;state.jwtDraft=JSON.stringify(parsed.payload,null,2);state.jwtResult=null;
      renderWorkspace();defaults();
    }
    if(id==='jwt-apply'){
      const parsed=parseLabJwt(state.jwtToken);
      let payload;
      try{payload=JSON.parse($('#jwt-payload').value);}catch{throw new Error('Payload geçerli JSON olmalı.');}
      if(!payload||Array.isArray(payload)||typeof payload!=='object')throw new Error('Payload bir JSON nesnesi olmalı.');
      const bytes=new TextEncoder().encode(JSON.stringify(payload));
      const part=btoa(Array.from(bytes,b=>String.fromCharCode(b)).join('')).replace(/\+/g,'-').replace(/\//g,'_').replace(/=+$/,'');
      const token=`${parsed.parts[0]}.${part}.${parsed.parts[2]}`;
      if(token.length>4096)throw new Error('Token çok uzun.');
      state.jwtToken=token;state.jwtDraft=JSON.stringify(payload,null,2);state.jwtResult=null;
      renderWorkspace();defaults();toast('Payload değişti; imza yeniden üretilmedi.');
    }
    if(id==='jwt-send')await executeRequest('GET',`/api/${state.mode}/jwt/invoices`,null);
    if(id==='jwt-copy'){
      try{await navigator.clipboard.writeText(state.jwtToken);toast('Token kopyalandı.');}
      catch{throw new Error('Token alanından seçip kopyalayabilirsin.');}
    }
  }));
}
