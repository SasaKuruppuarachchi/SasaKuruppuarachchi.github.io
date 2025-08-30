(function(){
  function renderPublications(listEl, pubs){
    listEl.innerHTML = '';
    pubs.forEach(function(p){
      var li = document.createElement('li');
      var titleHTML = p.url ? '<a href="'+p.url+'" target="_blank" rel="noopener noreferrer">'+p.title+'</a>' : p.title;
      li.innerHTML = '<strong>' + titleHTML + '</strong>' +
        (p.authors ? ', ' + p.authors : '') + (p.year? ' ('+p.year+')' : '') + '<br>' +
        (p.venue? '<em>'+p.venue+'</em>' : '');
      listEl.appendChild(li);
    });
  }
  document.addEventListener('DOMContentLoaded', function(){
    var targetOL = document.querySelector('#two ol');
    if(!targetOL) return;
    fetch('data/publications.json?cacheBust='+Date.now())
      .then(function(r){ if(!r.ok) throw new Error('HTTP '+r.status); return r.json(); })
      .then(function(json){
        if(Array.isArray(json) && json.length){
          json.sort(function(a,b){
            var ay = parseInt(a.year,10)||0; var by = parseInt(b.year,10)||0;
            if(by!==ay) return by-ay; // newest year first
            return (a.title||'').localeCompare(b.title||'');
          });
          renderPublications(targetOL, json);
        }
      })
      .catch(function(){ /* leave static fallback */ });
  });
})();
