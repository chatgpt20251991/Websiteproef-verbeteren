(() => {
  'use strict';
  const menuButton=document.querySelector('.menu-toggle');
  const menu=document.getElementById('mobile-menu');
  function setMenu(open){
    if(!menuButton||!menu)return;
    menu.hidden=!open;
    menuButton.setAttribute('aria-expanded',String(open));
    menuButton.setAttribute('aria-label',open?'Menu sluiten':'Menu openen');
  }
  if(menuButton){
    menuButton.addEventListener('click',()=>setMenu(menuButton.getAttribute('aria-expanded')!=='true'));
    menu.addEventListener('click',e=>{if(e.target.closest('a'))setMenu(false);});
    document.addEventListener('keydown',e=>{if(e.key==='Escape'&&!menu.hidden){setMenu(false);menuButton.focus();}});
    document.addEventListener('click',e=>{if(!menu.hidden&&!menu.contains(e.target)&&!menuButton.contains(e.target))setMenu(false);});
    matchMedia('(min-width:1025px)').addEventListener('change',e=>{if(e.matches)setMenu(false);});
  }
  function openHash(){
    const hash=location.hash.slice(1);
    if(!hash)return;
    const el=document.getElementById(hash);
    if(el&&el.tagName==='DETAILS')el.open=true;
  }
  openHash();window.addEventListener('hashchange',openHash);
  const form=document.getElementById('project-form');
  if(form){
    const query=new URLSearchParams(location.search);
    const service=query.get('dienst');
    if(service&&Array.from(form.elements.dienst.options).some(o=>o.value===service))form.elements.dienst.value=service;
    const part=query.get('onderdeel');
    if(part&&service&&form.elements.dienst.value===service)form.elements.vraag.value='Ik wil graag '+part.slice(0,150).toLowerCase()+' bespreken.\n\nMijn vraag:\n';
    let draft='';
    const status=document.getElementById('form-status');
    const copy=document.getElementById('copy-request');
    form.addEventListener('submit',e=>{
      e.preventDefault();
      if(!form.reportValidity())return;
      const data=new FormData(form);
      const select=form.elements.dienst;
      const selected=select.value?select.options[select.selectedIndex].text:'Nog te bespreken';
      const naam=String(data.get('naam')||'').trim();
      draft='Beste Avenzo Digital,\n\n'+String(data.get('vraag')||'').trim()+'\n\nNaam: '+naam+'\nOrganisatie: '+String(data.get('organisatie')||'').trim()+'\nE-mail: '+String(data.get('email')||'').trim()+'\nOnderwerp: '+selected+'\n';
      const subject='Projectaanvraag — '+selected;
      window.location.href='mailto:info@avenzodigital.nl?subject='+encodeURIComponent(subject)+'&body='+encodeURIComponent(draft);
      status.textContent='Je e-mail staat klaar om te openen. Opent er geen mailprogramma? Kopieer de aanvraag en mail die naar info@avenzodigital.nl.';
      copy.hidden=false;
    });
    copy.addEventListener('click',async()=>{
      try{await navigator.clipboard.writeText(draft);status.textContent='Aanvraagtekst gekopieerd. Je kunt die nu in je e-mail plakken.';}
      catch{status.textContent='Kopiëren lukt hier niet. Selecteer en kopieer je tekst uit het veld hierboven.';form.elements.vraag.focus();form.elements.vraag.select();}
    });
  }
})();
