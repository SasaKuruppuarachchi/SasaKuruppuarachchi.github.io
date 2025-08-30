(function(){
  function renderWork(listEl, items, limit){
    listEl.innerHTML = '';
    items.slice(0, limit).forEach(function(item, idx){
      var art = document.createElement('article');
      art.className = (idx % 2 === 1 ? '6u$' : '6u') + ' 12u$(xsmall) work-item';
      art.innerHTML = '\n        <a href="'+item.url+'" class="image fit thumb" target="_blank">'+(item.thumb ? '<img src="'+item.thumb+'" alt="" />':'')+'</a>\n        <h3>'+item.title+'</h3>\n        <p><small>'+item.displayDate+'</small><br>'+item.description+'</p>\n      ';
      listEl.appendChild(art);
    });
  }

  function sortItems(items, mode){
    return items.slice().sort(function(a,b){
      if(mode==='oldest') return new Date(a.date)-new Date(b.date);
      return new Date(b.date)-new Date(a.date);
    });
  }

  function initWork(){
    if(!window.LEGACY_WORK_ITEMS) return;
    var container = document.getElementById('recent-work-list');
    if(!container) return; // not on this page
    var combined = window.LEGACY_WORK_ITEMS.slice();
    var showingAll = false;
    var currentSort = 'newest';
    var toggleBtn = document.getElementById('work-toggle');
    var sortSelect = document.getElementById('work-sort');
    function refresh(){
      var sorted = sortItems(combined, currentSort);
      renderWork(container, sorted, showingAll? sorted.length : 6);
      if(toggleBtn){ toggleBtn.textContent = showingAll? 'Show Less' : 'View More'; }
    }
    if(toggleBtn){ toggleBtn.addEventListener('click', function(e){ e.preventDefault(); showingAll = !showingAll; refresh(); }); }
    if(sortSelect){ sortSelect.addEventListener('change', function(){ currentSort = sortSelect.value; refresh(); }); }
    refresh(); // initial
    // Fetch blog posts and merge
    fetchAndMergeBlogPosts(combined, refresh);
  }

  function fetchAndMergeBlogPosts(targetArray, onDone){
    var feedUrl = 'https://sasakuruppu.wordpress.com/feed/';
    var placeholderThumb = 'images/thumbs/01.jpg';
    function addItems(posts){
      posts.forEach(function(p){ targetArray.push(p); });
      if(onDone) onDone();
    }
    function mapToWorkItems(rawItems){
      return rawItems.slice(0,10).map(function(it){
        var d = new Date(it.pubDate || it.pubdate || it.date || '');
        var iso = isNaN(d)? new Date().toISOString().slice(0,10): d.toISOString().slice(0,10);
        var display = isNaN(d)? '' : d.toLocaleDateString(undefined,{year:'numeric', month:'short', day:'numeric'});
        var excerpt = truncate(stripHTML(it.description || it.content || ''), 140);
        return {
          id: 'blog-'+iso+'-'+(it.title||'').replace(/[^a-z0-9]+/gi,'-').toLowerCase(),
          title: it.title || 'Post',
          date: iso,
          displayDate: display,
          url: it.link || '#',
          category: 'Blog',
          tags: [],
          description: excerpt,
          thumb: placeholderThumb
        };
      });
    }
    function stripHTML(html){ var tmp=document.createElement('div'); tmp.innerHTML=html; return tmp.textContent||tmp.innerText||''; }
    function truncate(t,n){ return t.length>n? t.slice(0,n-3)+'...': t; }
    // Try XML
    fetch(feedUrl).then(function(r){ if(!r.ok) throw new Error('HTTP '+r.status); return r.text(); })
      .then(function(xmlText){
        var parser=new DOMParser(); var doc=parser.parseFromString(xmlText,'application/xml');
        if(doc.querySelector('parsererror')) throw new Error('Parse error');
        var items = Array.prototype.slice.call(doc.getElementsByTagName('item')).map(function(x){
          return {
            title: x.getElementsByTagName('title')[0]?.textContent,
            link: x.getElementsByTagName('link')[0]?.textContent,
            description: x.getElementsByTagName('description')[0]?.textContent,
            pubDate: x.getElementsByTagName('pubDate')[0]?.textContent
          };
        });
        addItems(mapToWorkItems(items));
      }).catch(function(){
        // Fallback to rss2json
        var proxy='https://api.rss2json.com/v1/api.json?rss_url='+encodeURIComponent(feedUrl);
        fetch(proxy).then(function(r){ if(!r.ok) throw new Error('Proxy HTTP '+r.status); return r.json(); })
          .then(function(json){ if(!json.items) throw new Error('No items'); addItems(mapToWorkItems(json.items)); })
          .catch(function(){ if(onDone) onDone(); });
      });
  }

  function truncate(s,n){ return s.length>n? s.slice(0,n-3)+'...': s; }
  function stripHTML(h){ var d=document.createElement('div'); d.innerHTML=h; return d.textContent||d.innerText||''; }

  // MEDIA (YouTube) - Try to fetch RSS feed (no API key). If blocked by CORS, show fallback note.
  function initMedia(){
    var mediaContainer = document.getElementById('media-videos');
    if(!mediaContainer) return;
    var channelId = mediaContainer.getAttribute('data-channel-id');
    if(!channelId || channelId === 'YOUR_CHANNEL_ID_HERE'){
      var note = document.createElement('p');
      note.innerHTML = 'Set your YouTube channel ID in data-channel-id to auto-load latest videos. <a href="https://www.youtube.com/@sasakuruppuarachchi/videos" target="_blank">Channel</a>.';
      mediaContainer.appendChild(note);
      return;
    }
    var rssUrl = 'https://www.youtube.com/feeds/videos.xml?channel_id=' + channelId;
    // Show loading indicator
    mediaContainer.innerHTML = '<p>Loading latest videos...</p>';
    // First attempt direct RSS (may fail CORS)
    fetch(rssUrl).then(function(r){
      if(!r.ok) throw new Error('HTTP '+r.status); return r.text();
    }).then(function processXML(xmlText){
      var parser = new DOMParser();
      var doc = parser.parseFromString(xmlText, 'application/xml');
      if(doc.querySelector('parsererror')) throw new Error('Parse error');
      var entries = Array.prototype.slice.call(doc.getElementsByTagName('entry')).slice(0,6);
      if(!entries.length) throw new Error('No entries');
      renderVideoEntries(entries.map(function(entry){
        return {
          title: entry.getElementsByTagName('title')[0]?.textContent || 'Video',
            videoId: entry.getElementsByTagName('yt:videoId')[0]?.textContent,
            published: entry.getElementsByTagName('published')[0]?.textContent
        };
      }));
    }).catch(function(){
      // Fallback to rss2json proxy (public). Rate limited; acceptable for light personal site use.
      var proxy = 'https://api.rss2json.com/v1/api.json?rss_url=' + encodeURIComponent(rssUrl);
      fetch(proxy).then(function(r){ if(!r.ok) throw new Error('Proxy HTTP '+r.status); return r.json(); })
        .then(function(json){
          if(!json.items) throw new Error('No items');
          var items = json.items.slice(0,6).map(function(it){
            // Extract video ID from link (watch?v=)
            var vid = (it.link.match(/v=([^&]+)/)||[])[1];
            return { title: it.title, videoId: vid, published: it.pubDate};
          }).filter(function(v){return v.videoId;});
          if(!items.length) throw new Error('No vids');
          renderVideoEntries(items);
        }).catch(function(){
          mediaContainer.innerHTML='';
          var note = document.createElement('p');
          note.innerHTML = 'Could not auto-load videos (CORS). <a href="https://www.youtube.com/@sasakuruppuarachchi/videos" target="_blank">View on YouTube</a>. ' +
            'Option: add a small serverless proxy later.';
          mediaContainer.appendChild(note);
        });
    });

    function renderVideoEntries(items){
      mediaContainer.innerHTML='';
      items.forEach(function(item, idx){
        var url = 'https://youtu.be/' + item.videoId;
        var thumb = 'https://i.ytimg.com/vi/'+item.videoId+'/hqdefault.jpg';
        var art = document.createElement('article');
        art.className = (idx % 2 === 1 ? '6u$' : '6u') + ' 12u$(xsmall) work-item';
        var dateStr='';
        if(item.published){
          var d = new Date(item.published);
          if(!isNaN(d)) dateStr = d.toLocaleDateString(undefined,{year:'numeric', month:'short', day:'numeric'});
        }
        art.innerHTML = '\n<a href="'+url+'" class="image fit thumb" target="_blank"><img src="'+thumb+'" alt="" /></a>'+
          '\n<h3>'+item.title+'</h3>\n<p><small>'+dateStr+'</small></p>';
        mediaContainer.appendChild(art);
      });
    }
  }

  document.addEventListener('DOMContentLoaded', function(){
    initWork();
    initMedia();
  });
})();
