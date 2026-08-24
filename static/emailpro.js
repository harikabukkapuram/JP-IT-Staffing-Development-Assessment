async function uploadCSV(){
 const f=document.getElementById('csv').files[0]; if(!f)return alert('Choose a CSV file.');
 const fd=new FormData();fd.append('file',f);
 const r=await fetch('/api/email/upload',{method:'POST',body:fd});const d=await r.json();
 if(!r.ok)return alert(d.error); document.getElementById('uploadMsg').textContent=d.message;
 document.getElementById('total').textContent=d.total;document.getElementById('business').textContent=d.business;document.getElementById('individual').textContent=d.individual;
}
async function classify(){
 const r=await fetch('/api/email/classify',{method:'POST'});const d=await r.json();
 if(!r.ok)return alert(d.error);
 document.getElementById('business').textContent=d.business;document.getElementById('individual').textContent=d.individual;
 document.getElementById('classifyResult').innerHTML=`<div class="result">${d.business} business + ${d.individual} individual emails classified.</div>`;
}
async function campaign(){
 const payload={subject:subject.value,audience:audience.value,content:content.value};
 const r=await fetch('/api/email/campaign',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
 const d=await r.json(); if(!r.ok)return alert(d.error); campaignMsg.textContent=d.message+` ${d.campaign.sent} recipients processed.`;
}
async function reports(){
 const d=await (await fetch('/api/email/reports')).json();
 reportTable.innerHTML=d.campaigns.length?`<table><tr><th>Subject</th><th>Audience</th><th>Sent</th><th>Created</th></tr>${d.campaigns.map(x=>`<tr><td>${x.subject}</td><td>${x.audience}</td><td>${x.sent}</td><td>${x.created}</td></tr>`).join('')}</table>`:'No campaigns yet.';
}
