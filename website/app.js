'use strict';
const $ = selector => document.querySelector(selector);
const websiteConfig=window.EBOSS_CONFIG||{apiOrigin:'',sourceCatalog:'/api/sources'};
const apiURL=route=>(websiteConfig.apiOrigin||'')+route;
const samples = {
  all: [['Business permits','What do I need to renew my business permit?'],['Building & occupancy','Unsa ang requirements para sa occupancy permit?'],['Fire safety','Paano mag-apply ng fire safety inspection certificate?']],
  business: [['New business','What documents do I need for a new business permit?'],['Renewal','Unsa ang requirements sa pag-renew sa business permit?'],['Business changes','Ano ang proseso para sa pagbabago ng business address?']],
  building: [['Occupancy','What are the requirements for an occupancy permit?'],['Building permits','Asa ko magsumite sa requirements sa building permit?'],['Permit fees','Ano ang fees para sa fencing permit?']],
  fire: [['Fire safety','How do I apply for an FSIC for business renewal?'],['Requirements','Unsa ang requirements para sa FSEC?'],['Fees','Magkano ang fees para sa FSIC for occupancy?']],
  planning: [['Locational clearance','What do I need for a locational clearance?'],['Application','Asa ko mo-apply og locational clearance?'],['Procedure','Ano ang steps sa pag-apply ng locational clearance?']],
  treasury: [['Community tax','How do I get a Community Tax Certificate?'],['Payment','Asa ko magbayad sa business permit fees?'],['Requirements','Ano ang requirements para kumuha ng cedula?']]
};
let busy = false, ready = false, activeView = 'ask', pendingRequest = null;
const conversation = $('#conversation');
function el(tag, className, text) {const node=document.createElement(tag);if(className)node.className=className;if(text!==undefined)node.textContent=text;return node;}
function showView(view) {
  activeView = ['ask','sources','about'].includes(view) ? view : 'ask';
  document.querySelectorAll('.view').forEach(n=>n.hidden=n.id!=='view-'+activeView);
  document.querySelectorAll('.nav-link').forEach(n=>{const current=n.dataset.view===activeView;n.classList.toggle('active',current);if(current)n.setAttribute('aria-current','page');else n.removeAttribute('aria-current');});
  if(activeView==='sources')loadSources();
}
window.addEventListener('hashchange',()=>showView(location.hash.slice(1)));
function renderSamples(service) {
  $('#suggestions').replaceChildren();
  samples[service].forEach(([label,question])=>{
    const button=el('button','suggestion');button.type='button';button.append(el('small','',label),el('span','question-text',question),el('span','arrow','↗'));
    button.addEventListener('click',()=>{$('#question').value=question;$('#question').focus();});$('#suggestions').append(button);
  });
}
document.querySelectorAll('[data-service]').forEach(button=>button.addEventListener('click',()=>{
  document.querySelectorAll('[data-service]').forEach(n=>{const current=n===button;n.classList.toggle('selected',current);n.setAttribute('aria-pressed',String(current));});
  renderSamples(button.dataset.service);
}));renderSamples('all');

async function checkHealth() {
  try {
    const response=await fetch(apiURL('/health'),{signal:AbortSignal.timeout(6000)});
    if(!response.ok)throw Error('health');const data=await response.json();ready=data.status==='ready';
    $('#connection-label').textContent=ready?'Assistant is ready':data.status==='starting'?'Loading charter sources':'Answer service unavailable';
    $('#connection-note').textContent=data.message||'The answer service is unavailable.';
    $('#connection-note').hidden=ready;$('#status-dot').className='status-dot '+(ready?'ready':'offline');
  } catch (_) {ready=false;$('#connection-label').textContent='Unable to connect';$('#connection-note').textContent='The assistant is not connected. Start the website server or try again shortly.';$('#connection-note').hidden=false;$('#status-dot').className='status-dot offline';}
  $('#send').disabled=busy||!ready;document.body.classList.toggle('not-ready',!ready);
}
$('#check-connection').addEventListener('click',checkHealth);checkHealth();setInterval(()=>{if(!document.hidden&&!busy)checkHealth();},15000);
function scrollToLatest(){conversation.lastElementChild?.scrollIntoView({behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'instant':'smooth',block:'nearest'});}
function message(type,text) {
  document.body.classList.add('chat-started');const article=el('article','message '+type);
  const label=el('div','message-label');if(type!=='user')label.append(el('span','avatar','e'));label.append(document.createTextNode(type==='user'?'YOU':'eBOSS'));
  const body=el('div','message-body',text);article.append(label,body);conversation.append(article);scrollToLatest();return article;
}
function addEvidence(article,citations) {
  if(!Array.isArray(citations)||!citations.length)return;
  const details=el('details','evidence');details.append(el('summary','',`View source passages (${citations.length})`));
  const list=el('div','evidence-list');citations.forEach(source=>{
    const card=el('section','source-card');card.dataset.citation=source.citation;
    card.append(el('h3','',`[${source.citation}] ${source.file_source}`));
    card.append(el('blockquote','',typeof source.text==='string'?source.text:'Passage text is unavailable.'));
    const page=source.pdf_relative_page,printed=source.source_page;
    const label=`Open PDF${Number.isInteger(page)?' · page '+page:''}${printed!=null?' · printed '+printed:''} ↗`;
    // Accept only the server's fixed source routes, never an arbitrary model URL.
    if(typeof source.source_url==='string'&&/^\/sources\/(business|treasury|building|fire|planning)\.pdf(?:#page=\d+)?$/.test(source.source_url)){
      const a=el('a','',label);a.href=source.source_url;a.target='_blank';a.rel='noopener noreferrer';card.append(a);
    } else card.append(el('span','',`PDF page ${page??'not recorded'}`));list.append(card);
  });details.append(list);article.append(details);
}
function renderAnswer(article,text,citations) {
  const body=article.querySelector('.message-body');body.replaceChildren();
  const valid=new Set(citations.map(c=>c.citation));
  // Text nodes preserve the archived answer; only valid bracketed citation labels become buttons.
  text.split(/(\[S\d+(?:,\s*S\d+)*\])/g).forEach(part=>{
    const labels=part.match(/S\d+/g);
    if(/^\[S/.test(part)&&labels?.every(label=>valid.has(label))){
      const button=el('button','citation-link',part);button.type='button';button.setAttribute('aria-label','Show source '+labels.join(', '));
      button.addEventListener('click',()=>{const details=article.querySelector('.evidence');if(details){details.open=true;const card=Array.from(details.querySelectorAll('.source-card')).find(c=>c.dataset.citation===labels[0]);card?.scrollIntoView({block:'nearest'});}});body.append(button);
    }else body.append(document.createTextNode(part));
  });
}
$('#question-form').addEventListener('submit',async event=>{
  event.preventDefault();const question=$('#question').value.trim();if(!question||busy)return;
  if(!ready){checkHealth();return;}
  busy=true;$('#send').disabled=true;$('#new-question').disabled=true;$('#question').disabled=true;
  message('user',question);$('#question').value='';const pending=message('assistant pending','Checking your question and charter sources…');
  pending.querySelector('.message-body').prepend(el('span','loading-dot'));pending.setAttribute('aria-busy','true');
  pendingRequest=new AbortController();const timer=setTimeout(()=>pendingRequest?.abort(),260000);
  try {
    const response=await fetch(apiURL('/api/query'),{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({query:question,response_language:$('#response-language').value}),signal:pendingRequest.signal});
    let data;try{data=await response.json();}catch(_){throw Error('The server returned an unreadable response. Please try again.');}
    if(!response.ok)throw Error(typeof data.detail==='string'?data.detail:'The question could not be processed. Please try again.');
    const text=data.status==='CLARIFICATION_REQUIRED'?(data.clarification_prompt||data.answer):data.answer;
    if(typeof text!=='string'||!text.trim())throw Error('No answer was returned. Please try again.');
    pending.className='message assistant';pending.removeAttribute('aria-busy');const citations=Array.isArray(data.citations)?data.citations:[];
    renderAnswer(pending,text,citations);
    const notice={CLARIFICATION_REQUIRED:'Please resend your full question with the specific service and details. Each question is processed independently.',GENERATION_INCOMPLETE:'This answer was cut short. Treat it as incomplete and check the source passages.',NO_SUPPORTED_ANSWER:'The retrieved passages did not support a complete answer. Try naming the service and the specific requirement you need.',CONTEXT_BUDGET_EXCEEDED:'Try asking about one specific step or requirement.'}[data.status];
    if(notice)pending.append(el('p','notice',notice));
    if(data.status.endsWith('_ERROR'))pending.classList.add('error');
    if(data.citation_labels_valid===false&&data.status==='ANSWERED')pending.append(el('p','notice','The answer’s citation labels could not be matched reliably. Check the source passages before relying on it.'));
    addEvidence(pending,citations);
    const copy=el('button','copy-answer','Copy answer');copy.type='button';copy.addEventListener('click',async()=>{try{await navigator.clipboard.writeText(text);copy.textContent='Copied';setTimeout(()=>copy.textContent='Copy answer',1600);}catch(_){copy.textContent='Select the answer text to copy';}});pending.append(copy);
  }catch(error){pending.className='message assistant error';pending.removeAttribute('aria-busy');pending.querySelector('.message-body').textContent=error.name==='AbortError'?'This request took too long. Please try again shortly.':error.message;$('#question').value=question;}
  finally{clearTimeout(timer);pendingRequest=null;busy=false;$('#new-question').disabled=false;$('#question').disabled=false;$('#send').disabled=!ready;scrollToLatest();}
});
$('#question').addEventListener('keydown',event=>{if(event.key==='Enter'&&!event.shiftKey&&!event.isComposing){event.preventDefault();$('#question-form').requestSubmit();}});
$('#new-question').addEventListener('click',()=>{if(busy)return;conversation.replaceChildren();document.body.classList.remove('chat-started');$('#question').value='';location.hash='ask';showView('ask');$('#question').focus();});
let libraryLoaded=false;
async function loadSources(){
  if(libraryLoaded)return;const container=$('#source-library');container.textContent='Loading the source library…';
  try{const response=await fetch(websiteConfig.sourceCatalog||'/api/sources');if(!response.ok)throw Error();const sources=await response.json();container.replaceChildren();
    sources.forEach(source=>{if(!/^\/sources\/[a-z]+\.pdf$/.test(source.url))return;const a=el('a','library-card');a.href=source.url;a.target='_blank';a.rel='noopener noreferrer';const text=el('div');text.append(el('h2','',source.office),el('p','',source.filename));a.append(el('span','library-icon','▤'),text,el('span','','↗'));container.append(a);});libraryLoaded=true;
  }catch(_){container.textContent='The source library could not be loaded. Please check your connection and reopen this tab.';}
}
showView(location.hash.slice(1));
