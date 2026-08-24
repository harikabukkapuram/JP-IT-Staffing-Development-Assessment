async function searchLeads(){
 const r=await fetch('/api/leads/search',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({query:query.value,country:country.value,limit:limit.value})});
 const d=await r.json();if(!r.ok)return alert(d.error);found.textContent=d.count;
 leadTable.innerHTML=`<table><tr><th>Name</th><th>Email</th><th>Phone</th><th>Country</th><th>Source</th><th>Action</th></tr>${d.leads.map(x=>`<tr><td>${x.name}</td><td>${x.email}</td><td>${x.phone}</td><td>${x.country}</td><td>${x.source}</td><td><button onclick="to.value='${x.email}'">Send</button></td></tr>`).join('')}</table>`;
}
async function uploadPDF(){
 const f=pdf.files[0];if(!f)return alert('Choose a PDF.');const fd=new FormData();fd.append('pdf',f);
 const r=await fetch('/api/leads/pdf',{method:'POST',body:fd});const d=await r.json();if(!r.ok)return alert(d.error);pdfPreview.textContent=d.preview||'No extractable text found.';
}
async function exportPDF(){const r=await fetch('/api/leads/export',{method:'POST'});if(!r.ok)return alert('Search leads first.');const b=await r.blob();const a=document.createElement('a');a.href=URL.createObjectURL(b);a.download='lead_report.pdf';a.click();}
async function sendEmail(){
 const r=await fetch('/api/leads/email',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({to:to.value,subject:emailSubject.value,body:emailBody.value})});
 const d=await r.json();if(!r.ok)return alert(d.error);emailMsg.textContent=d.message;
}
