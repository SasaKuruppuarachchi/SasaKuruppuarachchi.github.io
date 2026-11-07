/* Sasanka Kuruppu Arachchige — site interactions. No dependencies. */
(function () {
  'use strict';

  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };
  var root = document.documentElement;
  var body = document.body;
  var reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var canHover = window.matchMedia('(hover: hover) and (pointer: fine)').matches;
  var saveData = !!(navigator.connection && navigator.connection.saveData);
  var vt = function (fn) {
    if (document.startViewTransition && !reduceMotion) return document.startViewTransition(fn);
    fn(); return null;
  };

  /* ---------- Theme toggle ---------- */
  $$('.theme-toggle').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var current = root.getAttribute('data-theme') ||
        (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
      var next = current === 'dark' ? 'light' : 'dark';
      vt(function () {
        root.setAttribute('data-theme', next);
        try { localStorage.setItem('theme', next); } catch (e) {}
      });
    });
  });

  /* ---------- Scroll state (sticky glass bar, collapsing tagline) ---------- */
  var topbar = $('#topbar');
  var ticking = false;
  var scrollHandlers = [];
  function onScroll() {
    if (ticking) return;
    ticking = true;
    requestAnimationFrame(function () {
      var y = window.scrollY || window.pageYOffset;
      body.classList.toggle('is-scrolled', y > 90);
      if (topbar) topbar.classList.toggle('is-stuck', y > 4);
      scrollHandlers.forEach(function (fn) { fn(y); });
      ticking = false;
    });
  }
  window.addEventListener('scroll', onScroll, { passive: true });
  window.addEventListener('resize', onScroll, { passive: true });

  /* ---------- Sidebar table of contents + scrollspy ---------- */
  var toc = $('#toc');
  var tocList = toc && $('.toc__list', toc);
  var tocTargets = [];
  var tocLinks = [];
  var indicator = null;
  var activeIdx = -1;

  function slugify(s) {
    return s.toLowerCase().trim().replace(/[^\w\s-]/g, '').replace(/\s+/g, '-').slice(0, 60);
  }

  function buildToc() {
    if (!toc) return;
    var targets = $$('[data-toc]').filter(function (el) { return !el.hidden && el.offsetParent !== null; });
    if (!targets.length && body.classList.contains('layout-post')) {
      targets = $$('.prose h2').filter(function (h) { return h.textContent.trim(); });
      targets.forEach(function (h, i) {
        if (!h.id) h.id = slugify(h.textContent) || 'section-' + i;
        h.setAttribute('data-toc-label', h.textContent.trim());
      });
    }
    tocTargets = targets;
    tocList.innerHTML = '';
    tocLinks = targets.map(function (el) {
      var li = document.createElement('li');
      var a = document.createElement('a');
      a.href = '#' + el.id;
      a.textContent = el.getAttribute('data-toc') || el.getAttribute('data-toc-label') || el.textContent.trim();
      li.appendChild(a);
      tocList.appendChild(li);
      return a;
    });
    indicator = document.createElement('span');
    indicator.className = 'toc__indicator';
    indicator.setAttribute('aria-hidden', 'true');
    tocList.appendChild(indicator);
    toc.hidden = targets.length < 2;
    activeIdx = -1;
    spy(window.scrollY || 0);
  }

  function spy() {
    if (!tocTargets.length || toc.hidden) return;
    var line = window.innerHeight * 0.3;
    var idx = 0;
    for (var i = 0; i < tocTargets.length; i++) {
      if (tocTargets[i].getBoundingClientRect().top - line <= 0) idx = i;
    }
    var doc = document.documentElement;
    if (window.innerHeight + window.scrollY >= doc.scrollHeight - 4) idx = tocTargets.length - 1;
    if (idx === activeIdx) return;
    activeIdx = idx;
    tocLinks.forEach(function (a, i) {
      a.classList.toggle('is-active', i === idx);
      if (i === idx) a.setAttribute('aria-current', 'true'); else a.removeAttribute('aria-current');
    });
    var link = tocLinks[idx];
    if (link && indicator) {
      indicator.style.transform = 'translateY(' + link.offsetTop + 'px)';
      indicator.style.height = link.offsetHeight + 'px';
      indicator.style.opacity = '1';
      /* keep the active entry visible in long lists */
      var lt = link.offsetTop, lb = lt + link.offsetHeight;
      if (lt < tocList.scrollTop || lb > tocList.scrollTop + tocList.clientHeight) {
        tocList.scrollTo({ top: lt - tocList.clientHeight / 2, behavior: reduceMotion ? 'auto' : 'smooth' });
      }
    }
  }
  scrollHandlers.push(spy);
  document.addEventListener('toc:refresh', buildToc);

  /* ---------- Reveal on scroll ---------- */
  var revealIO = null;
  if (!reduceMotion && 'IntersectionObserver' in window) {
    revealIO = new IntersectionObserver(function (entries) {
      var batch = entries.filter(function (e) { return e.isIntersecting; });
      batch.forEach(function (e, i) {
        e.target.style.setProperty('--d', Math.min(i, 6) * 0.06 + 's');
        e.target.classList.add('in');
        revealIO.unobserve(e.target);
      });
    }, { rootMargin: '0px 0px -6% 0px', threshold: 0.01 });
  }
  function reveal(els) {
    els.forEach(function (el) { if (revealIO) revealIO.observe(el); else el.classList.add('in'); });
  }
  reveal($$('.reveal'));

  /* ---------- Animated card previews (hover on desktop, in-view on touch) ---------- */
  function animFor(media) {
    var poster = $('img', media);
    if (!poster || !poster.dataset.anim) return null;
    var anim = $('.card__anim', media);
    if (!anim) {
      anim = new Image();
      anim.className = 'card__anim';
      anim.alt = '';
      anim.decoding = 'async';
      media.insertBefore(anim, poster.nextSibling);
    }
    return { poster: poster, anim: anim };
  }
  function play(media) {
    var p = animFor(media);
    if (!p) return;
    media._want = true;
    if (p.anim.dataset.ready) { media.classList.add('is-playing'); return; }
    if (p.anim.dataset.loading) return;
    p.anim.dataset.loading = '1';
    p.anim.onload = function () {
      p.anim.dataset.ready = '1';
      if (media._want) media.classList.add('is-playing');
    };
    p.anim.src = p.poster.dataset.anim;
  }
  function stop(media) { media._want = false; media.classList.remove('is-playing'); }

  function wirePreviews(scope) {
    if (reduceMotion || saveData) return;
    var medias = $$('.card__media', scope).filter(function (m) { var i = $('img[data-anim]', m); return i && !m._wired; });
    medias.forEach(function (m) { m._wired = true; });
    if (canHover) {
      medias.forEach(function (m) {
        var link = m.closest('a') || m;
        link.addEventListener('mouseenter', function () { play(m); });
        link.addEventListener('mouseleave', function () { stop(m); });
        link.addEventListener('focus', function () { play(m); });
        link.addEventListener('blur', function () { stop(m); });
      });
    } else if ('IntersectionObserver' in window) {
      var io = new IntersectionObserver(function (entries) {
        entries.forEach(function (e) {
          if (e.isIntersecting) { e.target._t = setTimeout(function () { play(e.target); }, 250); }
          else { clearTimeout(e.target._t); stop(e.target); }
        });
      }, { rootMargin: '-30% 0px -30% 0px', threshold: 0 });
      medias.forEach(function (m) { io.observe(m); });
    }
  }
  wirePreviews(document);

  /* ---------- Filtering & sorting project grids ---------- */
  $$('[data-filter]').forEach(function (chips) {
    var sel = chips.getAttribute('data-filter');
    var grid = $(sel);
    if (!grid) return;
    var limit = parseInt(grid.getAttribute('data-limit') || '0', 10);
    var withYears = grid.hasAttribute('data-years');
    var sortCtl = $('[data-sort="' + sel + '"]');
    var cards = $$('.card', grid);
    var countEl = $('[data-count]', grid.closest('section'));
    var allLink = $('[data-all-link]', grid.closest('section'));
    var state = { cat: '__all', order: 'newest' };

    var params = new URLSearchParams(location.search);
    var topic = params.get('topic');
    if (topic) {
      var preset = $('.chip[data-label="' + topic + '"]', chips);
      if (preset) state.cat = preset.getAttribute('data-cat');
    }

    function render() {
      var match = cards.filter(function (c) {
        return state.cat === '__all' || (c.getAttribute('data-cats') || '').split('|').indexOf(state.cat) !== -1;
      });
      match.sort(function (a, b) {
        var d = (+a.getAttribute('data-date')) - (+b.getAttribute('data-date'));
        return state.order === 'oldest' ? d : -d;
      });
      var shown = limit ? match.slice(0, limit) : match;
      $$('.year-divider, .empty', grid).forEach(function (n) { n.remove(); });
      cards.forEach(function (c) { c.hidden = shown.indexOf(c) === -1; });
      var lastYear = null;
      shown.forEach(function (c) {
        var y = c.getAttribute('data-year');
        if (withYears && y !== lastYear) {
          var h = document.createElement('h3');
          h.className = 'year-divider';
          h.id = 'y' + y;
          h.setAttribute('data-toc', y);
          h.textContent = y;
          grid.appendChild(h);
          lastYear = y;
        }
        grid.appendChild(c);
        c.classList.add('in');
      });
      if (!shown.length) {
        var e = document.createElement('p');
        e.className = 'empty';
        e.textContent = 'Nothing here yet.';
        grid.appendChild(e);
      }
      if (countEl) countEl.textContent = limit ? (shown.length < match.length ? shown.length + ' of ' + match.length : match.length) : match.length;
      if (allLink) {
        var chip = $('.chip[aria-pressed="true"]', chips);
        var label = chip && chip.getAttribute('data-label');
        allLink.href = allLink.href.split('?')[0] + (label ? '?topic=' + label : '');
      }
      $$('.chip', chips).forEach(function (b) { b.setAttribute('aria-pressed', String(b.getAttribute('data-cat') === state.cat)); });
      wirePreviews(grid);
    }

    function update() {
      cards.forEach(function (c, i) { if (!c.hidden) c.style.viewTransitionName = 'card-' + i; });
      var t = vt(function () {
        render();
        cards.forEach(function (c, i) { c.style.viewTransitionName = c.hidden ? '' : 'card-' + i; });
      });
      var done = function () {
        cards.forEach(function (c) { c.style.viewTransitionName = ''; });
        document.dispatchEvent(new Event('toc:refresh'));
      };
      if (t && t.finished) t.finished.then(done, done); else done();
    }

    chips.addEventListener('click', function (ev) {
      var b = ev.target.closest('.chip');
      if (!b || b.getAttribute('data-cat') === state.cat) return;
      state.cat = b.getAttribute('data-cat');
      b.scrollIntoView({ block: 'nearest', inline: 'nearest', behavior: reduceMotion ? 'auto' : 'smooth' });
      update();
      if (!limit && history.replaceState) {
        var label = b.getAttribute('data-label');
        history.replaceState(null, '', location.pathname + (label ? '?topic=' + label : ''));
      }
    });
    if (sortCtl) {
      sortCtl.addEventListener('click', function (ev) {
        var b = ev.target.closest('button');
        if (!b || b.getAttribute('data-order') === state.order) return;
        state.order = b.getAttribute('data-order');
        moveSegment(sortCtl, b);
        update();
      });
    }
    if (state.cat !== '__all' || limit) render();
  });

  /* Small segmented controls: move the pill to the pressed segment. */
  function moveSegment(group, btn) {
    var pill = $('.segmented__pill', group);
    $$('button', group).forEach(function (x) { x.setAttribute('aria-pressed', String(x === btn)); });
    if (!pill) return;
    var from = pill.getBoundingClientRect();
    btn.insertBefore(pill, btn.firstChild);
    var to = pill.getBoundingClientRect();
    if (reduceMotion || !pill.animate) return;
    pill.animate([
      { transform: 'translateX(' + (from.left - to.left) + 'px)', width: from.width + 'px' },
      { transform: 'none', width: to.width + 'px' }
    ], { duration: 420, easing: 'cubic-bezier(0.34, 1.36, 0.64, 1)' });
  }

  /* Publication type filter */
  $$('[data-pub-filter]').forEach(function (group) {
    var list = $(group.getAttribute('data-pub-filter'));
    if (!list) return;
    group.addEventListener('click', function (ev) {
      var b = ev.target.closest('button');
      if (!b || b.getAttribute('aria-pressed') === 'true') return;
      moveSegment(group, b);
      var type = b.getAttribute('data-type');
      vt(function () {
        $$('.pub', list).forEach(function (li) {
          li.hidden = type !== 'all' && li.getAttribute('data-type') !== type;
          li.classList.add('in');
        });
      });
    });
  });

  /* BibTeX toggles */
  document.addEventListener('click', function (ev) {
    var b = ev.target.closest('[data-toggle-bib]');
    if (!b) return;
    var box = document.getElementById(b.getAttribute('aria-controls'));
    if (!box) return;
    var open = !box.classList.contains('is-open');
    box.classList.toggle('is-open', open);
    b.setAttribute('aria-expanded', String(open));
  });

  /* ---------- Copy to clipboard ---------- */
  document.addEventListener('click', function (ev) {
    var b = ev.target.closest('[data-copy]');
    if (!b || !navigator.clipboard) return;
    navigator.clipboard.writeText(b.getAttribute('data-copy')).then(function () {
      var html = b.innerHTML;
      b.textContent = '✓ Copied';
      b.classList.add('pill--published');
      setTimeout(function () { b.innerHTML = html; b.classList.remove('pill--published'); }, 1600);
    });
  });

  /* ---------- Lightbox (images in posts, YouTube videos) ---------- */
  var lb = $('#lightbox');
  var stage = lb && $('.lightbox__stage', lb);
  var caption = lb && $('.lightbox__caption', lb);
  var gallery = [];
  var gIndex = 0;

  function navBtn(dir) {
    var b = document.createElement('button');
    b.type = 'button';
    b.className = 'lightbox__nav lightbox__nav--' + dir;
    b.setAttribute('aria-label', dir === 'prev' ? 'Previous image' : 'Next image');
    b.innerHTML = dir === 'prev' ? '&#8249;' : '&#8250;';
    b.addEventListener('click', function (e) { e.stopPropagation(); step(dir === 'prev' ? -1 : 1); });
    return b;
  }
  var prevBtn, nextBtn;
  if (lb) {
    prevBtn = navBtn('prev'); nextBtn = navBtn('next');
    lb.appendChild(prevBtn); lb.appendChild(nextBtn);
  }

  function openLb() {
    if (!lb.open) {
      if (lb.showModal) lb.showModal(); else lb.setAttribute('open', '');
      body.classList.add('lb-open');
    }
  }
  function closeLb() {
    if (!lb.open) return;
    lb.classList.add('is-closing');
    setTimeout(function () {
      lb.classList.remove('is-closing');
      if (lb.close) lb.close(); else lb.removeAttribute('open');
      stage.innerHTML = '';
      body.classList.remove('lb-open');
    }, reduceMotion ? 0 : 200);
  }
  function showImage(i) {
    gIndex = (i + gallery.length) % gallery.length;
    var item = gallery[gIndex];
    var img = new Image();
    img.src = item.src;
    img.alt = item.alt || '';
    stage.innerHTML = '';
    stage.appendChild(img);
    caption.textContent = item.caption || '';
    var multi = gallery.length > 1;
    prevBtn.hidden = nextBtn.hidden = !multi;
    if (img.animate && !reduceMotion) img.animate([{ opacity: 0, transform: 'scale(.98)' }, { opacity: 1, transform: 'none' }], { duration: 280, easing: 'ease-out' });
  }
  function step(d) { if (gallery.length > 1) showImage(gIndex + d); }

  if (lb) {
    lb.addEventListener('click', function (e) {
      if (e.target === lb || e.target === stage || e.target.closest('[data-close]')) closeLb();
    });
    lb.addEventListener('cancel', function (e) { e.preventDefault(); closeLb(); });
    document.addEventListener('keydown', function (e) {
      if (!lb.open) return;
      if (e.key === 'ArrowLeft') step(-1);
      if (e.key === 'ArrowRight') step(1);
    });
    var tx = null;
    lb.addEventListener('touchstart', function (e) { tx = e.touches[0].clientX; }, { passive: true });
    lb.addEventListener('touchend', function (e) {
      if (tx === null) return;
      var dx = e.changedTouches[0].clientX - tx;
      if (Math.abs(dx) > 50) step(dx < 0 ? 1 : -1);
      tx = null;
    });

    /* Post images */
    var isImg = function (href) { return /\.(jpe?g|png|gif|webp|avif)(\?.*)?$/i.test(href || ''); };
    var proseImgs = $$('.prose img').filter(function (img) {
      var a = img.closest('a');
      return !a || isImg(a.getAttribute('href'));
    });
    proseImgs.forEach(function (img) { img.classList.add('zoomable'); });
    document.addEventListener('click', function (ev) {
      var img = ev.target.closest('.prose img.zoomable');
      if (!img) return;
      ev.preventDefault();
      gallery = proseImgs.map(function (im) {
        var a = im.closest('a');
        var fig = im.closest('figure');
        var cap = fig && $('figcaption', fig);
        return {
          src: (a && isImg(a.getAttribute('href')) ? a.getAttribute('href') : (im.currentSrc || im.src)).replace(/\?w=\d+$/, ''),
          alt: im.alt,
          caption: cap ? cap.textContent.trim() : im.alt
        };
      });
      openLb();
      showImage(proseImgs.indexOf(img));
    });

    /* Videos */
    document.addEventListener('click', function (ev) {
      var v = ev.target.closest('[data-video]');
      if (!v) return;
      ev.preventDefault();
      gallery = [];
      prevBtn.hidden = nextBtn.hidden = true;
      var f = document.createElement('iframe');
      f.src = 'https://www.youtube-nocookie.com/embed/' + encodeURIComponent(v.getAttribute('data-video')) + '?autoplay=1&rel=0&modestbranding=1';
      f.title = v.getAttribute('data-title') || 'YouTube video';
      f.allow = 'accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share';
      f.allowFullscreen = true;
      stage.innerHTML = '';
      stage.appendChild(f);
      caption.textContent = v.getAttribute('data-title') || '';
      openLb();
    });
  }

  /* ---------- Lazy, autoplaying loop videos (<video data-lazy> with <source data-src>) ---------- */
  var lazyVideos = $$('video[data-lazy]');
  if (lazyVideos.length) {
    var loadVideo = function (v) {
      $$('source[data-src]', v).forEach(function (s) { s.src = s.getAttribute('data-src'); s.removeAttribute('data-src'); });
      v.load();
    };
    if ('IntersectionObserver' in window) {
      var vio = new IntersectionObserver(function (entries) {
        entries.forEach(function (e) {
          var v = e.target;
          if (e.isIntersecting) {
            if (v.querySelector('source[data-src]')) loadVideo(v);
            if (v.hasAttribute('data-autoplay') && !reduceMotion) { var pr = v.play(); if (pr && pr.catch) pr.catch(function () {}); }
          } else if (v.hasAttribute('data-autoplay')) { v.pause(); }
        });
      }, { rootMargin: '200px 0px' });
      lazyVideos.forEach(function (v) { vio.observe(v); });
    } else { lazyVideos.forEach(loadVideo); }
  }

  /* ---------- Init ---------- */
  buildToc();
  onScroll();
  window.addEventListener('load', function () { activeIdx = -1; spy(); });
})();
