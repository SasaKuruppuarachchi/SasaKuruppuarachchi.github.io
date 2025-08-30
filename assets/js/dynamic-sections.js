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
    var all = sortItems(window.LEGACY_WORK_ITEMS,'newest');
    var container = document.getElementById('recent-work-list');
    if(!container) return;
    var showingAll = false;
    var currentSort = 'newest';
    var toggleBtn = document.getElementById('work-toggle');
    var sortSelect = document.getElementById('work-sort');
    function refresh(){
      var sorted = sortItems(window.LEGACY_WORK_ITEMS, currentSort);
      renderWork(container, sorted, showingAll? sorted.length : 6);
      if(toggleBtn){
        toggleBtn.textContent = showingAll? 'Show Less' : 'View More';
      }
    }
    if(toggleBtn){
      toggleBtn.addEventListener('click', function(e){
        e.preventDefault();
        showingAll = !showingAll;
        refresh();
      });
    }
    if(sortSelect){
      sortSelect.addEventListener('change', function(){
        currentSort = sortSelect.value;
        refresh();
      });
    }
    refresh();
  }

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
    fetch(rssUrl).then(function(r){
      if(!r.ok) throw new Error('HTTP '+r.status); return r.text();
    }).then(function(xmlText){
      var parser = new DOMParser();
      var doc = parser.parseFromString(xmlText, 'application/xml');
      var entries = Array.prototype.slice.call(doc.getElementsByTagName('entry')).slice(0,6);
      if(!entries.length) throw new Error('No entries');
      mediaContainer.innerHTML='';
      entries.forEach(function(entry, idx){
        var linkEl = entry.getElementsByTagName('link')[0];
        var titleEl = entry.getElementsByTagName('title')[0];
        var publishedEl = entry.getElementsByTagName('published')[0];
        var videoId = (entry.getElementsByTagName('yt:videoId')[0]||{}).textContent;
        var url = linkEl ? linkEl.getAttribute('href') : (videoId? 'https://youtu.be/'+videoId : '#');
        var thumb = videoId? 'https://i.ytimg.com/vi/'+videoId+'/hqdefault.jpg' : '';
        var art = document.createElement('article');
        art.className = (idx % 2 === 1 ? '6u$' : '6u') + ' 12u$(xsmall) work-item';
        var dateStr = '';
        if(publishedEl){
          var d = new Date(publishedEl.textContent);
            dateStr = d.toLocaleDateString(undefined,{year:'numeric', month:'short', day:'numeric'});
        }
        art.innerHTML = '\n<a href="'+url+'" class="image fit thumb" target="_blank">'+(thumb? '<img src="'+thumb+'" alt="" />':'')+'</a>\n<h3>'+ (titleEl? titleEl.textContent : 'Video') +'</h3>\n<p><small>'+dateStr+'</small></p>';
        mediaContainer.appendChild(art);
      });
    }).catch(function(err){
      mediaContainer.innerHTML='';
      var note = document.createElement('p');
      note.innerHTML = 'Could not auto-load videos (CORS or ID issue). <a href="https://www.youtube.com/@sasakuruppuarachchi/videos" target="_blank">View on YouTube</a>.';
      mediaContainer.appendChild(note);
    });
  }

  document.addEventListener('DOMContentLoaded', function(){
    initWork();
    initMedia();
  });
})();
