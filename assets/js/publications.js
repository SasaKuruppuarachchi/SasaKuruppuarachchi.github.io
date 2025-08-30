(function(){
  function renderPublications(listEl, pubs){
    listEl.innerHTML = '';
    pubs.forEach(function(p){
      var li = document.createElement('li');
      var titleHTML = p.url ? '<a href="'+p.url+'" target="_blank" rel="noopener noreferrer">'+p.title+'</a>' : p.title;
      var yearLabel = p.year ? (' ('+p.year+')') : ' (In press)';
      var doiBadge = '';
      if(p.doi){
        var doiUrl = p.doi.startsWith('http') ? p.doi : ('https://doi.org/'+p.doi.replace(/^https?:\/\/doi.org\//,'').replace(/^doi:\s*/i,''));
        doiBadge = ' <a class="doi-badge" href="'+doiUrl+'" target="_blank" rel="noopener noreferrer">DOI</a>';
      }
      li.innerHTML = '<strong>' + titleHTML + '</strong>' +
        (p.authors ? ', ' + p.authors : '') + yearLabel + '<br>' +
        (p.venue? '<em>'+p.venue+'</em>' : '') + doiBadge;
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
