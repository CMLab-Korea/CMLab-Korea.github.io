/* CMLab website: dependency-free client interactions. All research content is editable JSON. */
(() => {
  'use strict';
  const $ = (s, p=document) => p.querySelector(s);
  const $$ = (s, p=document) => [...p.querySelectorAll(s)];
  const page = document.body.dataset.page;
  const nav = $('.nav-links');
  const toggle = $('.menu-toggle');
  if (toggle && nav) {
    function setMenu(open) {
      nav.classList.toggle('open', open);
      toggle.setAttribute('aria-expanded', String(open));
      toggle.setAttribute('aria-label', open ? 'Close navigation' : 'Open navigation');
    }
    toggle.addEventListener('click', () => setMenu(!nav.classList.contains('open')));
    document.addEventListener('keydown', event => {
      if (event.key === 'Escape' && nav.classList.contains('open')) {
        setMenu(false);
        toggle.focus();
      }
    });
  }
  $$('[data-nav]').forEach(link => {
    if (link.dataset.nav === page) {
      link.classList.add('active');
      link.setAttribute('aria-current', 'page');
    }
  });
  const progress = $('#scroll-progress');
  const onScroll = () => {
    const max = document.documentElement.scrollHeight - innerHeight;
    if (progress) progress.style.width = (max > 0 ? (scrollY / max * 100) : 0).toFixed(2) + '%';
  };
  addEventListener('scroll', onScroll, {passive:true});onScroll();
  if ('IntersectionObserver' in window) {
    const o = new IntersectionObserver((entries) => entries.forEach(e => {if (e.isIntersecting) {e.target.classList.add('in-view');o.unobserve(e.target)}}), {threshold:.08});
    $$('.reveal').forEach(el => o.observe(el));
  } else {$$('.reveal').forEach(el=>el.classList.add('in-view'))}

  function putStat(name, value) {
    if (!Number.isSafeInteger(value) || value < 0) return;
    $$(`[data-stat="${name}"]`).forEach(el => {el.textContent = value.toLocaleString('en-US')});
  }
  window.cmlabScholarStatsApply = stats => {
    if (!stats || stats.scholar_author_id !== 'D5yPXMsAAAAJ') return;
    if (!Number.isSafeInteger(stats.citations) || !Number.isSafeInteger(stats.h_index) || stats.h_index>stats.citations) return;
    putStat('citations',stats.citations);putStat('h_index',stats.h_index);
  };
  if ($('[data-stat="citations"], [data-stat="h_index"]')) {
    const tag = document.createElement('script');
    tag.async = true;
    tag.src = 'https://cmlab-korea.github.io/cmlab-web-assets/data/scholar-stats.js?v=' + Math.floor(Date.now() / 3600000);
    tag.onerror = () => console.info('Live metrics temporarily unavailable; showing verified fallback values.');
    document.head.appendChild(tag);
  }

  /* Import only repository-owned JSON, never executable page HTML. */
  async function getData(file) {
    const r = await fetch('data/'+file, {cache:'no-cache'});
    if (!r.ok) throw Error(`Unable to load ${file}`);
    return r.json();
  }
  function node(tag, cls, content) {const n=document.createElement(tag);if(cls)n.className=cls;if(content!==undefined)n.textContent=content;return n}
  function safeURL(value) {try{const u=new URL(value,location.href);return ['https:','http:'].includes(u.protocol)?u.href:'#'}catch{return '#'}}

  function watchProjectDates(projects, render) {
    const koreaDate = new Intl.DateTimeFormat('sv-SE', {
      timeZone: 'Asia/Seoul', year: 'numeric', month: '2-digit', day: '2-digit'
    });
    let previousDate;
    let timer;

    function update() {
      clearTimeout(timer);
      const now = Date.now();
      const date = koreaDate.format(now);
      if (date !== previousDate) {
        previousDate = date;
        const groups = {ongoing: [], completed: [], upcoming: []};
        for (const project of projects) {
          const phase = project.start > date ? 'upcoming'
            : project.end < date.slice(0, project.end.length) ? 'completed' : 'ongoing';
          groups[phase].push(project);
        }
        render(groups);
      }
      const [year, month, day] = date.split('-').map(Number);
      const nextMidnight = Date.UTC(year, month - 1, day + 1) - 9 * 60 * 60 * 1000;
      timer = setTimeout(update, nextMidnight - now);
    }

    document.addEventListener('visibilitychange', () => {
      if (!document.hidden) update();
    });
    update();
  }

  if ($('[data-stat="manuscripts"]')) {
    getData('research-output.json').then(({manuscripts_in_preparation: count}) => {
      putStat('manuscripts', count);
      const badge = $('.preprint-manuscript-count');
      if (badge && Number.isSafeInteger(count) && count >= 0) badge.hidden = false;
    }).catch(() => { /* The count stays unavailable if the data cannot be loaded. */ });
  }

  function authorNames(authors = '') {
    return authors.split(/,\s*(?:and\s+)?|\s+and\s+/i)
      .map(name => name.trim().replace(/\+(?=[*†‡+]*$)/g, '†')).filter(Boolean);
  }

  async function getPublications() {
    const papers = await getData('publications.json');
    const conferences = papers.filter(paper => paper.type === 'Conference').length;
    const journals = papers.filter(paper => paper.type === 'Journal').length;
    putStat('conference', conferences);
    putStat('journal', journals);
    putStat('total', conferences + journals);
    putStat('preprint', papers.filter(paper => paper.type === 'Preprint').length);
    return papers;
  }

  function paperTitleParts(paper) {
    const [prefix, ...rest] = paper.title.split(':');
    if (rest.length && identityKey(prefix) === identityKey(paper.short || '')) {
      return {nickname: prefix.trim(), title: rest.join(':').trim()};
    }
    return {title: paper.title};
  }

  function mediaURL(path) {
    return path.startsWith('assets/') ? path.split('/').map(encodeURIComponent).join('/') : path;
  }

  function paperMedia(paper, imageClass, videoClass, controls) {
    if (!paper.teaser_video) {
      return paper.teaser ? photo(mediaURL(paper.teaser), imageClass, paper.teaser_alt || '') : null;
    }
    const video = node('video', videoClass);
    video.src = mediaURL(paper.teaser_video);
    video.controls = controls;
    video.playsInline = video.defaultMuted = video.muted = video.loop = true;
    video.preload = controls ? 'none' : 'metadata';
    if (paper.teaser) video.poster = mediaURL(paper.teaser);
    video.setAttribute('aria-label', paper.teaser_video_label || `${paper.short || paper.title} teaser`);
    return video;
  }

  if (page==='home') {
    const research = $('#what-we-explore');
    const translation = $('.translation-card', research);
    const directions = $$('.translation-path a', translation).map(link => ({
      link, card: document.getElementById(link.hash.slice(1))
    }));
    const hover = matchMedia('(hover: hover)');

    function linkResearchDirection() {
      const focused = directions.find(({link, card}) => link.matches(':focus-visible') || card.matches(':focus-visible'));
      const pointed = hover.matches && directions.find(({link, card}) => link.matches(':hover') || card.matches(':hover'));
      const active = focused || pointed || directions.find(({link}) => link.hash === location.hash);
      for (const direction of directions) {
        direction.link.classList.toggle('direction-linked', direction === active);
        direction.card.classList.toggle('direction-linked', direction === active);
      }
      translation.classList.toggle('direction-linked', Boolean(active));
      if (active) {
        translation.style.setProperty('--translation-accent', `var(--${active.card.id}-accent)`);
      }
    }

    for (const {link, card} of directions) {
      for (const target of [link, card]) {
        for (const event of ['pointerenter', 'pointerleave', 'focus', 'blur']) {
          target.addEventListener(event, () => requestAnimationFrame(linkResearchDirection));
        }
      }
    }
    addEventListener('hashchange', linkResearchDirection);
    linkResearchDirection();

    if ('IntersectionObserver' in window) {
      new IntersectionObserver(([entry]) => {
        translation.classList.toggle('translation-visible', entry.isIntersecting);
      }).observe(translation);
    } else {
      translation.classList.add('translation-visible');
    }

    const featured = $('#featured-work');
    const publications = getPublications();
    publications.then(items => {
      const pools = [
        items.filter(paper => paper.type === 'Preprint').slice(0, 6),
        items.filter(paper => paper.type !== 'Preprint').slice(0, 6)
      ];
      const controls = $('#selected-controls');
      const motion = matchMedia('(prefers-reduced-motion: reduce)');
      let paused = motion.matches;
      let previous = [];
      let timer;
      const mediaVisibility = 'IntersectionObserver' in window ? new IntersectionObserver(entries => {
        for (const entry of entries) {
          entry.target.dataset.visible = String(entry.isIntersecting);
          updateFeatureVideo(entry.target);
        }
      }, {threshold: .2}) : null;

      function updateFeatureVideo(video) {
        if (video.dataset.visible === 'true' && !document.hidden && !motion.matches && !paused) {
          video.play().catch(() => {});
        } else {
          video.pause();
        }
      }

      function choosePair(pool) {
        const fresh = pool.filter(paper => !previous.includes(paper.id));
        const available = [...(fresh.length >= 2 ? fresh : pool)];
        const selected = [];
        while (available.length && selected.length < 2) {
          const index = Math.floor(Math.random() * available.length);
          selected.push(available.splice(index, 1)[0]);
        }
        return selected;
      }

      function featureCard(paper) {
        const card = node('a', 'feature-card');
        const external = [paper.project_url, paper.venue_url, paper.arxiv_url]
          .find(url => url && !paper.unavailable_urls?.includes(url));
        card.href = external || 'publications.html#paper-' + paper.id;
        if (external) {
          card.target = '_blank';
          card.rel = 'noopener noreferrer';
        }
        const media = paperMedia(paper, 'feature-poster', 'feature-poster', false);
        if (media) {
          card.append(media);
        } else {
          const placeholder = node('span', 'feature-poster feature-placeholder', paper.short);
          placeholder.setAttribute('aria-hidden', 'true');
          card.append(placeholder);
        }
        const venue = node('p', 'feature-venue', paper.venue_short || paper.venue);
        if (paper.distinction && paper.distinction_percent) {
          venue.append(' · ', node('strong', 'feature-distinction', paper.distinction + ' · ' + paper.distinction_percent));
        }
        const {title} = paperTitleParts(paper);
        card.append(node('h3', 'feature-name', paper.short || title), venue);
        if (paper.short) card.append(node('p', 'feature-title', title));
        return card;
      }

      function showWorks() {
        const papers = pools.flatMap(choosePair);
        previous = papers.map(paper => paper.id);
        mediaVisibility?.disconnect();
        $$('video', featured).forEach(video => video.pause());
        featured.replaceChildren(...papers.map(featureCard));
        $$('video', featured).forEach(video => mediaVisibility?.observe(video));
        featured.closest('section').hidden = papers.length === 0;
      }

      function schedule() {
        clearTimeout(timer);
        pause.textContent = paused ? 'Resume' : 'Pause';
        $$('video', featured).forEach(updateFeatureVideo);
        if (paused || document.hidden || featured.matches(':hover, :focus-within')) return;
        timer = setTimeout(() => {
          showWorks();
          schedule();
        }, 5000);
      }

      const pause = node('button', 'selected-control');
      const next = node('button', 'selected-control', 'Next works');
      pause.type = next.type = 'button';
      pause.setAttribute('aria-controls', 'featured-work');
      next.setAttribute('aria-controls', 'featured-work');
      pause.addEventListener('click', () => {
        paused = !paused;
        schedule();
      });
      next.addEventListener('click', () => {
        showWorks();
        schedule();
      });
      for (const event of ['mouseenter', 'mouseleave', 'focusin']) featured.addEventListener(event, schedule);
      featured.addEventListener('focusout', () => setTimeout(schedule, 0));
      document.addEventListener('visibilitychange', schedule);
      motion.addEventListener('change', () => {
        paused = motion.matches;
        schedule();
      });
      controls.append(pause, next);
      controls.hidden = pools.every(pool => pool.length <= 2);
      showWorks();
      schedule();
    }).catch(() => { featured.textContent = 'Selected work is temporarily unavailable.'; });

    const news = $('#news-list');
    const filters = $('#news-filters');
    const more = $('#news-more');
    const initialNewsCount = 10;
    Promise.all([getData('news.json'), publications.catch(() => [])]).then(([items, papers]) => {
      const papersById = new Map(papers.map(paper => [paper.id, paper]));
      const categories = ['All', 'Publication', 'Award', 'People', 'Event'];
      const entries = items.filter(item => categories.includes(item.category))
        .sort((a, b) => b.date.slice(0, 7).localeCompare(a.date.slice(0, 7)));

      function categoryIcon(category) {
        const svgNamespace = 'http://www.w3.org/2000/svg';
        const icon = document.createElementNS(svgNamespace, 'svg');
        icon.setAttribute('class', 'news-icon');
        icon.setAttribute('aria-hidden', 'true');
        const use = document.createElementNS(svgNamespace, 'use');
        use.setAttribute('href', 'assets/img/news-icons.svg#' + category.toLowerCase());
        icon.append(use);
        return icon;
      }

      function renderHeadline(entry) {
        const parts = entry.headline;
        const headline = node('p', 'news-headline');
        const seen = new Set();
        for (const part of Array.isArray(parts) ? parts : [parts]) {
          if (typeof part === 'string') {
            headline.append(part);
          } else if (part.url) {
            const link = node('a', '', part.text);
            link.href = safeURL(part.url);
            seen.add(link.href);
            headline.append(link);
          } else {
            headline.append(node('strong', '', part.text));
          }
        }
        for (const {id} of entry.publication_updates || []) {
          const paper = papersById.get(id);
          if (!paper) continue;
          const card = 'publications.html#paper-' + id;
          const label = entry.publication_updates.length === 1 ? 'Publication card' : paper.short || paper.title;
          for (const [text, url] of [[label, card], ['Paper', paper.venue_url || paper.arxiv_url], ['Project', paper.project_url]]) {
            if (!url || paper.unavailable_urls?.includes(url)) continue;
            const href = safeURL(url);
            if (seen.has(href)) continue;
            const link = node('a', '', text);
            link.href = href;
            headline.append(' · ', link);
            seen.add(href);
          }
        }
        return headline;
      }

      let selection = 'All';
      let expanded = false;

      function renderNews() {
        const matches = entries.filter(item => selection === 'All' || item.category === selection);
        const visible = expanded ? matches : matches.slice(0, initialNewsCount);
        news.replaceChildren();
        let currentYear;
        let list;
        for (const entry of visible) {
          const [year, month, day] = entry.date.split('-');
          if (year !== currentYear) {
            currentYear = year;
            list = node('ul', 'news-year-list');
            news.append(node('h3', 'news-year', year), list);
          }
          const item = node('li', 'news-item');
          const dateParts = entry.show_day && day ? [month, day, year] : [month, year];
          const time = node('time', '', dateParts.join('/'));
          time.dateTime = entry.date;
          const category = node('span', 'news-category', entry.category);
          category.prepend(categoryIcon(entry.category));
          item.append(time, category, renderHeadline(entry));
          list.append(item);
        }
        if (!visible.length) news.append(node('p', 'muted', 'No updates in this category yet.'));
        more.hidden = matches.length <= initialNewsCount;
        more.setAttribute('aria-expanded', String(expanded));
        more.textContent = expanded ? 'Show fewer updates' : `Show all ${matches.length} updates`;
        for (const button of filters.querySelectorAll('button')) {
          button.setAttribute('aria-pressed', String(button.textContent === selection));
        }
      }

      for (const category of categories) {
        const button = node('button', 'news-filter', category);
        button.type = 'button';
        if (category !== 'All') button.prepend(categoryIcon(category));
        button.addEventListener('click', () => {
          selection = category;
          expanded = false;
          renderNews();
        });
        filters.append(button);
      }
      more.addEventListener('click', () => {
        expanded = !expanded;
        renderNews();
      });
      renderNews();
    }).catch(() => { news.textContent = 'Research updates are temporarily unavailable.'; });

    const canvas=$('#particle-canvas');
    if (canvas && !matchMedia('(prefers-reduced-motion: reduce)').matches) {
      const ctx=canvas.getContext('2d'); let dpr=1,w=0,h=0,pts=[];let visible=true;
      function resize(){const rect=canvas.getBoundingClientRect();dpr=Math.min(devicePixelRatio||1,2);w=rect.width;h=rect.height;canvas.width=Math.max(1,Math.round(w*dpr));canvas.height=Math.max(1,Math.round(h*dpr));ctx.setTransform(dpr,0,0,dpr,0,0);pts=Array.from({length:Math.min(65,Math.floor(w/7))},()=>({x:Math.random()*w,y:Math.random()*h,r:.4+Math.random()*1.4,s:.1+Math.random()*.27}))}
      resize(); if ('ResizeObserver' in window) new ResizeObserver(resize).observe(canvas);else addEventListener('resize',resize);
      document.addEventListener('visibilitychange',()=>{visible=!document.hidden});
      function frame(){if (visible){ctx.clearRect(0,0,w,h);ctx.fillStyle='rgba(163,195,255,.52)';for(const p of pts){p.y-=p.s;if(p.y<0)p.y=h;ctx.beginPath();ctx.arc(p.x,p.y,p.r,0,Math.PI*2);ctx.fill()}}requestAnimationFrame(frame)}requestAnimationFrame(frame);
    }
  }
  if (page === 'publications') {
    const search = $('#paper-search');
    const type = $('#paper-type');
    const year = $('#paper-year');
    const venue = $('#paper-venue');
    const area = $('#paper-area');
    const publicationList = $('#publication-list');
    const motion = matchMedia('(prefers-reduced-motion: reduce)');
    const visibleVideos = new Set();
    const viewerPaused = new WeakSet();
    const pagePaused = new WeakSet();
    const videoObserver = 'IntersectionObserver' in window ? new IntersectionObserver(entries => {
      for (const {target, intersectionRatio} of entries) {
        if (!target.isConnected) continue;
        if (intersectionRatio >= .2) {
          visibleVideos.add(target);
          playVisibleVideo(target);
        } else {
          visibleVideos.delete(target);
          pausePaperVideo(target);
        }
      }
    }, {threshold: .2}) : null;

    function playVisibleVideo(video) {
      if (!motion.matches && !document.hidden && !viewerPaused.has(video) && video.paused) {
        video.play().catch(() => {});
      }
    }

    function pausePaperVideo(video) {
      if (video.paused) return;
      pagePaused.add(video);
      video.pause();
    }

    function updateVisibleVideos() {
      for (const video of visibleVideos) {
        if (motion.matches || document.hidden) pausePaperVideo(video);
        else playVisibleVideo(video);
      }
    }

    document.addEventListener('visibilitychange', updateVisibleVideos);
    motion.addEventListener('change', updateVisibleVideos);

    function observePaperVideo(video) {
      video.addEventListener('pause', () => {
        if (!pagePaused.delete(video)) viewerPaused.add(video);
      });
      video.addEventListener('play', () => viewerPaused.delete(video));
      videoObserver?.observe(video);
    }

    let selectedArea = 'all';
    const identities = new Map();
    let institutions = {};
    const counter = $('#paper-count');
    const feedback = $('#paper-feedback');
    const areas = new Map([
      ['Pixel-Level Intelligence', {label: 'Pixel-Level', icon: 'pixel'}],
      ['Video & Motion Intelligence', {label: 'Video & Motion', icon: 'motion'}],
      ['3D/4D World Modeling', {label: '3D/4D World', icon: 'world'}],
      ['Generative & Agentic Visual AI', {label: 'Generative / Agentic AI', icon: 'agent'}]
    ]);
    const requestedArea = new URLSearchParams(location.search).get('area');
    const selected = [...areas].find(([, area]) => area.icon === requestedArea);
    if (selected) selectedArea = selected[0];

    function paperAreas(paper) {
      return [...new Set(paper.areas || [paper.area])].filter(name => areas.has(name));
    }

    function venueName(paper) {
      return venueBadge(paper).split("'")[0];
    }

    function venueBadge(paper) {
      return paper.venue_short;
    }

    function paperLinks(paper) {
      const links = new Map();
      const resources = [
        [venueBadge(paper), paper.venue_url],
        ['Project', paper.project_url],
        ['arXiv', paper.arxiv_url],
        ['Code', paper.code_url],
        ['Dataset', paper.dataset_url],
        ...(paper.additional_links || []).map(({label, url}) => [label, url])
      ];
      for (const [label, url] of resources) {
        if (url && /^https?:\/\//.test(url) && !links.has(url) && !paper.unavailable_urls?.includes(url)) {
          links.set(url, label);
        }
      }
      return links;
    }

    function externalLink(label, url, className) {
      const link = node('a', className, label);
      link.href = url;
      link.target = '_blank';
      link.rel = 'noopener noreferrer';
      return link;
    }

    function applyInstitutionColors(element, institution) {
      const colors = institution?.brand_colors;
      if (!Array.isArray(colors) || colors.length !== 3 || !colors.every(color => /^#[\da-f]{6}$/i.test(color))) return false;
      element.classList.add('institution-branded');
      colors.forEach((color, index) => element.style.setProperty('--institution-color-' + (index + 1), color));
      return true;
    }

    function authorLine(authors, organizations) {
      const line = node('p', 'paper-authors');
      const names = authorNames(authors);
      names.forEach((name, i) => {
        if (i) line.append(', ');
        const marks = name.match(/[†*‡]+$/)?.[0] || '';
        const plain = name.slice(0, name.length - marks.length).trim();
        const member = identities.get(identityKey(plain));
        const label = member?.author_name || plain;
        const author = member?.url ? externalLink(label, member.url, 'paper-author-link') : node('span', '', label);
        if (member?.local) {
          author.classList.add('paper-author-highlight');
          author.replaceChildren(node('span', 'paper-author-lab-name', label));
        } else {
          const institution = organizations?.get(member?.organization);
          if (applyInstitutionColors(author, institution)) {
            author.classList.add('paper-author-collaborator');
            author.title = institution.name;
          }
        }
        line.append(author);
        if (marks) line.append(node('sup', 'author-mark', marks));
      });
      return line;
    }

    function areaTag(name, iconOnly = false) {
      const {label, icon} = areas.get(name);
      const tag = node('span', 'paper-area');
      tag.append(symbol('assets/img/research-symbols.svg', icon));
      if (iconOnly) {
        tag.title = label;
        tag.append(node('span', 'visually-hidden', label));
      } else {
        tag.append(label);
      }
      return tag;
    }

    function paperRow(paper) {
      const row = node('article', 'paper-row rich-paper');
      row.id = 'paper-' + paper.id;
      if (paper.distinction_percent) row.classList.add('distinguished-paper');
      const badge = node('div', 'venue-column');
      if (paper.catalog_number) {
        const number = paper.type === 'Preprint' ? `[${paper.catalog_number}]` : paper.catalog_number;
        badge.append(node('span', `record-number record-${paper.type.toLowerCase()}`, number));
      }
      badge.append(node('span', 'venue-abbr', venueBadge(paper)));
      badge.append(node('span', 'venue-kind', paper.type === 'Preprint' ? String(paper.year) : paper.type));
      if (paper.distinction && paper.distinction_percent) {
        badge.append(node('span', 'paper-distinction', [paper.distinction, paper.distinction_percent].filter(Boolean).join(' · ')));
      }
      if (paper.venue.includes('Findings')) badge.append(node('span', 'venue-kind', 'Findings'));
      row.append(badge);

      const teaser = node('div', 'paper-teaser');
      const media = paperMedia(paper, 'paper-image', 'paper-video', true);
      if (media) teaser.append(media);
      else teaser.setAttribute('aria-hidden', 'true');
      row.append(teaser);

      const body = node('div', 'paper-rich-body');
      const links = paperLinks(paper);
      const destination = [paper.venue_url, paper.arxiv_url, paper.project_url].find(url => links.has(url));
      const heading = node('h3');
      const {nickname, title} = paperTitleParts(paper);
      const titleLabel = destination ? externalLink('', destination, 'paper-title') : heading;
      if (nickname) {
        titleLabel.append(node('span', 'paper-nickname', nickname), ': ');
      } else if (identityKey(paper.short || '') && !identityKey(title).startsWith(identityKey(paper.short))) {
        body.append(node('div', 'paper-overline', paper.short));
      }
      titleLabel.append(title);
      if (destination) heading.append(titleLabel);
      body.append(heading);
      const organizationIds = new Set(paper.organizations || []);
      if (paper.use_current_collaborator_affiliations) {
        for (const author of authorNames(paper.authors)) {
          const person = identities.get(identityKey(author));
          if (person && !person.local && person.organization) organizationIds.add(person.organization);
        }
      }
      const organizations = new Map([...organizationIds].filter(id => institutions[id]).map(id => [id, institutions[id]]));
      if (paper.authors) body.append(authorLine(paper.authors, organizations));
      const organizationsByName = new Map([...organizations.values()].map(org => [org.name, org]));
      const affiliationLabels = [...new Set([...(paper.affiliations || []), ...organizationsByName.keys()])];
      if (affiliationLabels.length) {
        const affiliations = node('div', 'paper-affiliations');
        affiliations.setAttribute('aria-label', 'Research collaborators');
        const icon = symbol('assets/img/news-icons.svg', 'collaboration');
        icon.classList.add('paper-collaboration-icon');
        affiliations.append(icon);
        for (const name of affiliationLabels) {
          const badge = node('span', 'affiliation-tag', name);
          const institution = organizationsByName.get(name);
          applyInstitutionColors(badge, institution);
          const logo = institution?.logo;
          if (logo) badge.prepend(photo(logo, 'paper-org-logo', ''));
          affiliations.append(badge);
        }
        body.append(affiliations);
      }
      if (links.size) {
        const resources = node('div', 'paper-meta');
        for (const [url, label] of links) resources.append(externalLink(label + ' ↗', url, 'paper-open'));
        body.append(resources);
      }
      if (paper.verification) {
        const review = node('p', 'paper-verification');
        const anchor = paper.verification.toLowerCase().replaceAll(' ', '-');
        const link = externalLink(paper.verification,
          'https://github.com/CMLab-Korea/CMLab-Korea.github.io/blob/main/PUBLICATIONS-REVIEW.md#' + anchor);
        review.append(link);
        body.append(review);
      }
      const tags = node('div', 'paper-areas');
      tags.append(...paperAreas(paper).map(name => areaTag(name, true)));
      if (tags.childElementCount) body.append(tags);
      row.append(body);
      return row;
    }

    const authorDirectory = Promise.all([
      getData('people.json').catch(() => []),
      getData('collaborators.json').catch(() => []),
      getData('institutions.json').catch(() => ({}))
    ]).then(([people, collaborators, organizations]) => {
      institutions = organizations;
      for (const person of collaborators) {
        for (const key of identityNames(person)) identities.set(key, person);
      }
      for (const person of people) {
        const profile = person.url || 'people.html#member-' + identityKey(person.name);
        for (const key of identityNames(person)) identities.set(key, {...person, local: true, url: profile});
      }
      identities.set(identityKey('Jihyong Oh'), {local: true, url: 'people.html#principal-investigator'});
    });

    Promise.all([getPublications(), authorDirectory]).then(([items]) => {
      for (const value of [...new Set(items.map(p => p.year))].sort((a, b) => b - a)) year.add(new Option(value, value));
      const venueCounts = new Map();
      for (const paper of items.filter(p => p.type !== 'Preprint')) {
        const name = venueName(paper);
        venueCounts.set(name, (venueCounts.get(name) || 0) + 1);
      }
      for (const [name, count] of [...venueCounts].sort(([a], [b]) => a.localeCompare(b))) {
        venue.add(new Option(name + ' (' + count + ')', name));
      }


      function render() {
        const query = search.value.trim().toLowerCase();
        const matches = items.filter(p => {
          const tags = paperAreas(p);
          const keywords = [p.short, p.title, p.authors, p.venue, venueBadge(p), p.distinction,
            ...tags, ...tags.map(name => areas.get(name).label)].join(' ').toLowerCase();
          return (type.value === 'all' || p.type === type.value)
            && (year.value === 'all' || String(p.year) === year.value)
            && (venue.value === 'all' || venueName(p) === venue.value)
            && (selectedArea === 'all' || tags.includes(selectedArea))
            && keywords.includes(query);
        });
        const preprints = matches.filter(p => p.type === 'Preprint');
        const published = matches.filter(p => p.type !== 'Preprint');
        videoObserver?.disconnect();
        visibleVideos.forEach(pausePaperVideo);
        visibleVideos.clear();
        $('#preprint-section').hidden = preprints.length === 0;
        $('#international-section').hidden = published.length === 0;
        $('#preprint-list').replaceChildren(...preprints.map(paperRow));
        $('#published-list').replaceChildren(...published.map(paperRow));
        $$('.paper-video', publicationList).forEach(observePaperVideo);
        counter.textContent = `${matches.length} of ${items.length} entries`;
        feedback.textContent = 'No publications match these filters.';
        feedback.hidden = matches.length > 0;
      }

      search.addEventListener('input', render);
      for (const select of [type, year, venue]) select.addEventListener('change', render);
      const summary = $('summary', area);
      const choices = $('.area-choices', area);
      if (selectedArea !== 'all') summary.replaceChildren(areaTag(selectedArea));
      for (const key of ['all', ...areas.keys()]) {
        const choice = node('button', 'area-choice');
        choice.type = 'button';
        choice.setAttribute('aria-pressed', String(key === selectedArea));
        choice.append(key === 'all' ? 'All areas' : areaTag(key));
        choice.addEventListener('click', () => {
          selectedArea = key;
          summary.replaceChildren(key === 'all' ? 'All areas' : areaTag(key));
          for (const button of choices.children) button.setAttribute('aria-pressed', String(button === choice));
          area.open = false;
          summary.focus();
          render();
        });
        choices.append(choice);
      }
      area.addEventListener('keydown', event => {
        if (event.key === 'Escape' && area.open) {
          area.open = false;
          summary.focus();
        }
      });
      document.addEventListener('click', event => {
        if (!area.contains(event.target)) area.open = false;
      });
      render();
      if (/^#paper-\d+$/.test(location.hash)) {
        document.getElementById(location.hash.slice(1))?.scrollIntoView();
      }
    }).catch(() => {
      counter.textContent = 'Publications unavailable';
      feedback.textContent = 'Try refreshing the page to load the publication list.';
      feedback.hidden = false;
    });

    const archive = $('#publication-archive');
    Promise.all([getData('publication-archive.json'), authorDirectory]).then(([records]) => {
      for (const list of $$('[data-records]', archive)) {
        const entries = records.filter(record => record.id.startsWith(list.dataset.records));
        list.replaceChildren(...entries.map(record => {
          const entry = node('li', 'archive-record');
          if (record.anchor) entry.id = record.anchor;
          entry.append(node('span', 'record-number record-' + record.id[0].toLowerCase(), record.id));
          const body = node('div');
          if (record.date) {
            const time = node('time', 'archive-date', record.date.replaceAll('-', '.'));
            time.dateTime = record.date;
            body.append(time);
          }
          if (record.title) {
            body.append(node('h4', 'archive-paper-title', record.title), authorLine(record.authors),
              node('p', 'archive-venue', record.venue));
          } else {
            body.append(node('p', '', record.text));
          }
          for (const {label, url} of record.links || []) {
            body.append(externalLink(label + ' ↗', safeURL(url), 'archive-link'));
          }
          entry.append(body);
          return entry;
        }));
      }
      for (const details of $$('details', archive)) {
        $('.archive-count', details).textContent = $$('.archive-record', details).length;
      }
      archive.hidden = false;

      function openArchivedRecord() {
        $('.archive-record.archive-current', archive)?.classList.remove('archive-current');
        const target = document.getElementById(location.hash.slice(1));
        const details = target?.closest('details');
        if (!target?.classList.contains('archive-record') || !details || !archive.contains(details)) return;
        details.open = true;
        target.classList.add('archive-current');
        target.scrollIntoView({block: 'start'});
      }

      openArchivedRecord();
      addEventListener('hashchange', openArchivedRecord);
    }).catch(() => {
      archive.replaceChildren(node('p', 'archive-notice', 'Additional publication records are temporarily unavailable.'));
      archive.hidden = false;
    });
  }

  if (page === 'projects') {
    const roles = {L: 'PI / Research Lead', U: 'Unit Lead', P: 'Participating Researcher'};
    const status = $('#projects-status');
    const formatDate = value => {
      const [year, month] = value.split('-');
      return [month, year].join('.');
    };

    function projectCard(project, organizations) {
      const card = node('article', 'project-card');
      card.id = 'project-' + project.id.toLowerCase();
      const meta = node('div', 'project-meta');
      const rolesLabel = node('span', 'project-role project-role-' + project.role.toLowerCase());
      rolesLabel.append(node('b', '', project.id), node('span', '', roles[project.role]));
      const dates = node('span', 'project-dates');
      for (const [index, date] of [project.start, project.end].entries()) {
        if (index) dates.append(' – ');
        const time = node('time', '', formatDate(date));
        time.dateTime = date;
        dates.append(time);
      }
      meta.append(rolesLabel, dates);

      const title = node('h3', '', project.title);
      title.lang = 'ko';
      card.append(meta, title);
      if (project.topic) card.append(node('p', 'project-topic', project.topic));
      if (project.lectures) card.append(node('p', 'project-topic', project.lectures));
      if (project.programs?.length) card.append(node('p', 'project-program', project.programs.join(' · ')));

      const support = node('div', 'project-support');
      support.append(node('span', 'project-tag', project.support_type));
      if (project.compute) support.append(node('span', 'project-tag', project.compute));
      if (project.reference) support.append(node('span', 'project-tag', project.reference));
      if (project.url) {
        const link = nameLink('Program ↗', safeURL(project.url), 'project-link');
        support.append(link);
      }
      card.append(support);

      const logos = node('ul', 'project-organizations');
      logos.setAttribute('aria-label', 'Project organizations');
      for (const key of project.organizations) {
        const org = organizations[key];
        if (!org) continue;
        const li = node('li');
        const mark = org.logo ? photo(org.logo, 'project-logo', org.name) : org.name;
        if (org.url) {
          const link = nameLink('', safeURL(org.url));
          link.append(mark);
          li.append(link);
        } else {
          li.append(mark);
        }
        logos.append(li);
      }
      card.append(logos);
      return card;
    }

    getData('projects.json').then(({projects, organizations}) => {
      const cards = new Map(projects.map(project => [project.id, projectCard(project, organizations)]));
      watchProjectDates(projects, groups => {
        for (const [phase, entries] of Object.entries(groups)) {
          const section = $('#' + phase + '-projects');
          $('.project-count', section).textContent = entries.length;
          $('.project-grid', section).replaceChildren(...entries.map(project => cards.get(project.id)));
          section.hidden = entries.length === 0;
          const jump = $(`.project-jumps a[href="#${section.id}"]`);
          $('.project-count', jump).textContent = entries.length;
          jump.hidden = section.hidden;
        }
      });
      status.hidden = true;
      if (location.hash) document.getElementById(location.hash.slice(1))?.scrollIntoView();
    }).catch(() => { status.textContent = 'Project information is temporarily unavailable.'; });
  }
  function identityKey(name) {
    return name.normalize('NFKC').toLowerCase().replace(/[^\p{L}\p{N}]/gu, '');
  }

  function identityNames(person) {
    return [person.name || person.person, ...(person.aliases || [])].map(identityKey);
  }

  function nameLink(name, url, className = 'profile-link') {
    if (!url) return node('span', '', name);
    const a = node('a', className, name);
    a.href = url;
    return a;
  }

  function photo(src, className, alt) {
    const img = node('img', className);
    img.src = src;
    img.alt = alt;
    img.loading = 'lazy';
    return img;
  }

  function symbol(path, id) {
    const namespace = 'http://www.w3.org/2000/svg';
    const svg = document.createElementNS(namespace, 'svg');
    const use = document.createElementNS(namespace, 'use');
    use.setAttribute('href', path + '#' + id);
    svg.setAttribute('aria-hidden', 'true');
    svg.append(use);
    return svg;
  }

  if (page === 'people') {
    getData('people.json').then(people => {
      const degreeRank = person => person.degree.startsWith('Ph.D.') ? 0 : 1;
      const sorted = [...people].sort((a, b) => degreeRank(a) - degreeRank(b)
        || a.semester.localeCompare(b.semester)
        || (a.sort_family_ko || '').localeCompare(b.sort_family_ko || '', 'ko')
        || a.name.localeCompare(b.name));
      for (const person of sorted) {
        const card = node('article', degreeRank(person) === 0 ? 'person-card phd-member' : 'person-card');
        card.id = 'member-' + identityKey(person.name);
        const semester = person.group === 'intern' ? '(' + person.semester + ')' : '[' + person.semester + ']';
        const heading = node('h3');
        heading.append(nameLink(person.name, person.url));
        if (person.photo) card.append(photo(person.photo, 'member-photo', person.name));
        card.append(heading,
          node('p', '', person.degree + ' ' + semester));
        if (person.note) card.append(node('small', 'member-note', person.note));
        if (person.email) card.append(nameLink('Email', 'mailto:' + person.email, 'profile-link member-email'));
        $('#' + person.group + '-people').append(card);
        if (person.alumni) {
          const {from, to, phd_since} = person.alumni;
          const alumni = node('article', 'alumni-card');
          const alumniName = node('h3');
          alumniName.append(nameLink(person.name, person.url));
          alumni.append(alumniName, node('p', '', 'M.S. · ' + from + ' → ' + to),
            node('p', 'member-note', 'Ph.D. candidate at CMLab · since ' + phd_since));
          $('#alumni').append(alumni);
        }
      }
      if (location.hash.startsWith('#member-')) document.getElementById(location.hash.slice(1))?.scrollIntoView();
    }).catch(() => { $('#core-people').textContent = 'Member profiles are temporarily unavailable.'; });

    Promise.all([getData('collaborators.json'), getData('institutions.json'), getPublications()])
      .then(([collaborators, institutions, papers]) => {
        const grid = $('#collaborators-grid');
        const organizationOrder = {
          Industry: ['microsoft', 'adobe', 'oracle', 'razer', 'flawless', 'naver-ai', 'naver-cloud', 'lunit', 'inshorts'],
          Academia: ['princeton', 'cornell-tech', 'kaist', 'snu', 'postech', 'khu', 'cau', 'konkuk']
        };
        for (const category of ['Industry', 'Academia', 'Research Institute']) {
          const group = collaborators.filter(p => p.category === category);
          const order = organizationOrder[category];
          if (order) {
            const rank = person => order.includes(person.organization)
              ? order.indexOf(person.organization) : order.length;
            group.sort((a, b) => rank(a) - rank(b));
          }
          if (!group.length) continue;
          const cards = node('div', 'collab-cards');
          for (const person of group) {
            const organization = institutions[person.organization] || {name: person.institution};
            const names = identityNames(person);
            const card = node('article', 'collab-card directory-card');
            const header = node('div', 'collab-card-header');
            const name = node('div', 'collab-identity');
            const heading = node('h4');
            heading.append(nameLink(person.person, person.url));
            name.append(heading, node('p', 'collab-organization', organization.name));
            const position = [person.role, person.unit].filter(Boolean).join(' · ');
            if (position) name.append(node('p', 'collab-position', position));
            header.append(name);
            const logo = organization.compact_logo || organization.logo;
            if (logo) {
              header.append(photo(logo, 'organization-logo', ''));
            }
            card.append(header);
            if (person.collaborative_lab) {
              const label = nameLink('Close research collaboration', person.lab_url, 'lab-partner');
              label.prepend(symbol('assets/img/news-icons.svg', 'collaboration'));
              card.append(label);
            }
            const works = node('div', 'collab-paper-links');
            if (person.ongoing) {
              const ongoing = node('span', 'lab-partner active-project', 'Active project');
              ongoing.prepend(symbol('assets/img/news-icons.svg', 'collaboration'));
              works.append(ongoing);
            }
            for (const paper of papers.filter(p => !person.exclude_paper_ids?.includes(p.id)
              && authorNames(p.authors).some(n => names.includes(identityKey(n))))) {
              const url = [paper.project_url, paper.venue_url, paper.arxiv_url]
                .find(value => value && !paper.unavailable_urls?.includes(value));
              works.append(nameLink(paper.short + ' [' + paper.venue_short + ']', url, 'profile-link'));
            }
            if (works.childElementCount) card.append(works);
            cards.append(card);
          }
          grid.append(node('h3', 'collaborator-group-heading', category), cards);
        }
      }).catch(() => { $('#collaborators-grid').textContent = 'Collaborator profiles are temporarily unavailable.'; });
  }

  if (page === 'teaching') {
    getData('courses.json').then(courses => {
      const history = $('#course-history');
      for (const semester of new Set(courses.map(course => course.semester))) {
        const [year, term] = semester.split('-');
        const group = node('section', 'course-semester');
        group.append(node('h2', '', (term === '1' ? 'Spring' : 'Fall') + ' 20' + year));
        const list = node('ul', 'course-list');
        for (const course of courses.filter(item => item.semester === semester)) {
          const entry = node('li', 'course-item');
          const text = node('div');
          text.append(node('h3', '', course.title), node('p', '', course.ko));
          entry.append(text, node('span', 'directory-meta', course.level + ' · ' + course.code));
          if (course.award) {
            const award = nameLink('Outstanding Instructor', course.award, 'course-award');
            award.prepend(symbol('assets/img/news-icons.svg', 'award'));
            entry.append(award);
          }
          list.append(entry);
        }
        group.append(list);
        history.append(group);
      }
    }).catch(() => { $('#course-history').textContent = 'Course history is temporarily unavailable.'; });
  }

  if (page === 'life') {
    const icons = new Map([['Conference', 'conference'], ['Seminar', 'seminar'],
      ['Lab gathering', 'people'], ['Milestone', 'award'], ['Outreach', 'event']]);
    const motionPreference = matchMedia('(prefers-reduced-motion: reduce)');
    const gallery = $('#gallery-events');
    const dialog = node('dialog', 'gallery-dialog');
    dialog.setAttribute('aria-labelledby', 'album-title');
    gallery.after(dialog);
    let openedPlayer;
    let opener;
    let previewsPaused = false;

    function galleryBadge(category) {
      const badge = node('span', 'gallery-category', category);
      if (icons.has(category)) badge.prepend(symbol('assets/img/news-icons.svg', icons.get(category)));
      return badge;
    }

    const month = new Intl.DateTimeFormat('en-US', {month: 'short', timeZone: 'UTC'});
    const isVideo = path => /\.(mp4|webm)$/i.test(path);

    function eventDate(event) {
      const start = new Date(event.date);
      const [year, , day] = event.date.split('-');
      if (!day) return new Intl.DateTimeFormat('en-US', {month: 'long', timeZone: 'UTC', year: 'numeric'}).format(start);
      const first = month.format(start) + ' ' + Number(day);
      if (!event.end_date || event.end_date === event.date) return first + ', ' + year;
      const end = new Date(event.end_date);
      const [, endMonth, endDay] = event.end_date.split('-');
      const last = Number(endDay) + ', ' + end.getUTCFullYear();
      if (end.getUTCFullYear() !== start.getUTCFullYear()) return first + ', ' + year + ' – ' + month.format(end) + ' ' + last;
      if (event.date.slice(5, 7) === endMonth) return first + '–' + last;
      return first + ' – ' + month.format(end) + ' ' + last;
    }

    function metadata(event) {
      const line = node('p', 'directory-meta');
      const time = node('time', '', eventDate(event));
      time.dateTime = event.date;
      line.append(time, ' · ', event.location);
      return line;
    }

    function albumPlayer(event, controls = false, initialIndex = 0) {
      const media = event.media || event.images || [];
      const frame = node('div', 'gallery-photo');
      let index = initialIndex;
      let displayedIndex = initialIndex;
      let timer;
      let visible = false;
      let paused = false;
      let touchStart;
      let current;
      let revision = 0;
      const status = node('span', 'gallery-count');
      const playback = node('button');
      playback.type = 'button';

      function refresh() {
        clearTimeout(timer);
        if (visible && !document.hidden && !motionPreference.matches && !paused && media.length > 1
            && (controls ? dialog.open : !dialog.open && !previewsPaused
              && !frame.parentElement?.matches(':hover, :focus-within'))) {
          timer = setTimeout(() => advance(1), 3000);
        }
      }

      function updatePlayback() {
        playback.textContent = paused ? 'Play slideshow' : 'Pause slideshow';
        playback.hidden = motionPreference.matches;
      }

      function advance(step) {
        if (!visible && step !== 0) return;
        clearTimeout(timer);
        index = (index + step + media.length) % media.length;
        const path = media[index];
        const isMovie = isVideo(path);
        const visual = isMovie && controls ? node('video') : isMovie ? node('span', 'gallery-video-label', 'Video')
          : photo(mediaURL(path), '', event.title + (media.length > 1 ? ' · photo ' + (index + 1) : ''));
        if (visual.tagName === 'VIDEO') {
          visual.src = mediaURL(path);
          visual.controls = visual.playsInline = true;
          visual.preload = 'metadata';
          visual.setAttribute('aria-label', event.title + ' video');
          visual.addEventListener('play', () => {
            paused = true;
            updatePlayback();
            refresh();
          });
        }
        visual.classList.add('gallery-slide');
        const request = ++revision;
        function show() {
          if (request !== revision) return;
          if (current?.tagName === 'VIDEO') current.pause();
          if (current) current.replaceWith(visual);
          else frame.prepend(visual);
          current = visual;
          displayedIndex = index;
          status.textContent = (index + 1) + ' / ' + media.length;
          refresh();
        }
        if (!isMovie && (current || controls)) visual.loading = 'eager';
        if (!isMovie && current) visual.decode().then(show, show);
        else show();
      }

      function select(step) {
        paused = true;
        updatePlayback();
        advance(step);
      }

      if (controls && media.length > 1) {
        const bar = node('div', 'gallery-controls');
        for (const [label, arrow, step] of [['Previous item', '←', -1], ['Next item', '→', 1]]) {
          const button = node('button', '', arrow);
          button.type = 'button';
          button.setAttribute('aria-label', label);
          button.addEventListener('click', () => select(step));
          bar.append(button);
          if (step === -1) bar.append(status);
        }
        playback.className = 'gallery-playback';
        playback.addEventListener('click', () => {
          paused = !paused;
          updatePlayback();
          refresh();
        });
        bar.append(playback);
        frame.append(bar);
        frame.addEventListener('pointerdown', event => {
          if (event.pointerType === 'touch' && !event.target.closest('button, video')) touchStart = event.clientX;
        });
        frame.addEventListener('pointerup', event => {
          const distance = event.clientX - touchStart;
          if (Math.abs(distance) > 50) select(distance > 0 ? -1 : 1);
          touchStart = undefined;
        });
        frame.addEventListener('pointercancel', () => { touchStart = undefined; });
      }
      advance(0);
      updatePlayback();
      return {
        frame, refresh, updatePlayback, select,
        get displayedIndex() { return displayedIndex; },
        setVisible(value) { visible = value; refresh(); }
      };
    }

    function eventLinks(event, papers) {
      const links = node('ul', 'gallery-links');
      for (const item of event.links || []) {
        const entry = node('li');
        const paper = papers.get(item.paper_id);
        if (paper) {
          const primary = [paper.project_url, paper.venue_url, paper.arxiv_url]
            .find(url => url && !paper.unavailable_urls?.includes(url));
          entry.append(nameLink(paper.short || paper.title, primary || 'publications.html#paper-' + paper.id));
          const venue = item.venue_label || paper.venue_short;
          if (venue) entry.append(' ', nameLink('[' + venue + ']', item.venue_url || paper.venue_url, 'gallery-venue-link'));
        } else if (item.label) {
          entry.append(nameLink(item.label, item.url));
        } else continue;
        links.append(entry);
      }
      return links;
    }

    Promise.all([
      getData('gallery.json'), getData('people.json').catch(() => []), getData('publications.json').catch(() => [])
    ]).then(([events, people, papers]) => {
      const paperDirectory = new Map(papers.map(paper => [paper.id, paper]));
      const directory = new Map(people.flatMap(person => identityNames(person).map(key => [key, person])));
      directory.set(identityKey('Jihyong Oh'), {name: 'Jihyong Oh', url: 'people.html#principal-investigator'});
      const players = new Map();
      const observer = 'IntersectionObserver' in window
        ? new IntersectionObserver(entries => entries.forEach(entry => {
          players.get(entry.target)?.setVisible(entry.isIntersecting);
        }), {threshold: .15})
        : null;

      function refreshAll() {
        for (const player of [...players.values(), openedPlayer].filter(Boolean)) {
          player.updatePlayback();
          player.refresh();
        }
      }

      function albumDetails(event) {
        const content = node('div', 'gallery-dialog-content');
        const heading = node('h2', '', event.title);
        heading.id = 'album-title';
        content.append(galleryBadge(event.category), heading, metadata(event));
        if (event.summary) content.append(node('p', '', event.summary));
        if (event.title_ko || event.summary_ko) {
          const korean = node('div', 'gallery-translation');
          korean.lang = 'ko';
          if (event.title_ko) korean.append(node('p', 'gallery-korean-title', event.title_ko));
          if (event.summary_ko) korean.append(node('p', '', event.summary_ko));
          content.append(korean);
        }
        if (event.participants?.length) {
          const names = node('p', 'gallery-people');
          event.participants.forEach((name, index) => {
            if (index) names.append(', ');
            const person = directory.get(identityKey(name));
            if (!person) {
              names.append(name);
              return;
            }
            const link = nameLink('', person.url, 'gallery-person-link');
            link.classList.add('paper-author-highlight');
            link.append(node('span', 'paper-author-lab-name', person.name));
            names.append(link);
          });
          content.append(names);
        }
        const links = eventLinks(event, paperDirectory);
        if (links.childElementCount) content.append(links);
        return content;
      }

      function openAlbum(event, trigger, initialIndex) {
        const close = node('button', 'gallery-close', 'Close');
        close.type = 'button';
        close.addEventListener('click', () => dialog.close());
        const content = albumDetails(event);
        dialog.replaceChildren(close);
        if (event.media?.length) {
          openedPlayer = albumPlayer(event, true, initialIndex);
          dialog.append(openedPlayer.frame);
        }
        dialog.append(content);
        opener = trigger;
        dialog.showModal();
        openedPlayer?.setVisible(true);
        refreshAll();
      }

      dialog.addEventListener('close', () => {
        openedPlayer?.setVisible(false);
        dialog.querySelector('video')?.pause();
        openedPlayer = undefined;
        opener?.focus({preventScroll: true});
        refreshAll();
      });
      dialog.addEventListener('click', event => {
        if (event.target === dialog) dialog.close();
      });
      dialog.addEventListener('keydown', event => {
        if (!openedPlayer || event.target.closest('video')) return;
        if (['ArrowLeft', 'ArrowRight'].includes(event.key) && $('.gallery-controls', dialog)) {
          event.preventDefault();
          openedPlayer.select(event.key === 'ArrowLeft' ? -1 : 1);
        }
      });
      document.addEventListener('visibilitychange', refreshAll);
      motionPreference.addEventListener('change', refreshAll);

      const cards = events.map(event => {
        const card = node('article', 'gallery-card');
        card.id = event.id;
        if (event.media?.length) {
          const player = albumPlayer(event);
          players.set(card, player);
          card.append(player.frame);
          for (const signal of ['pointerenter', 'pointerleave', 'focusin', 'focusout']) {
            card.addEventListener(signal, () => requestAnimationFrame(player.refresh));
          }
          if (observer) observer.observe(card);
          else player.setVisible(true);
        }
        const body = node('div', 'gallery-card-body');
        const badges = node('div', 'gallery-card-badges');
        badges.append(galleryBadge(event.category));
        if (event.catalog_number) badges.append(node('span', 'gallery-number', '[' + event.catalog_number + ']'));
        const expand = node('span', 'gallery-expand-mark', '↗');
        expand.setAttribute('aria-hidden', 'true');
        badges.append(expand);
        const heading = node('h3', '', event.title);
        body.append(badges, heading, metadata(event));
        if (event.summary) body.append(node('p', 'gallery-summary', event.summary));
        if (event.media?.length) {
          const photos = event.media.filter(path => !isVideo(path)).length;
          const videos = event.media.length - photos;
          const count = [];
          if (photos) count.push(photos + (photos === 1 ? ' photo' : ' photos'));
          if (videos) count.push(videos + (videos === 1 ? ' video' : ' videos'));
          body.append(node('p', 'gallery-media-total', count.join(' · ')));
        }
        const trigger = node('button', 'gallery-open');
        trigger.type = 'button';
        trigger.setAttribute('aria-label', 'Open ' + event.title + ', ' + eventDate(event));
        trigger.setAttribute('aria-haspopup', 'dialog');
        trigger.addEventListener('click', () => openAlbum(event, trigger, players.get(card)?.displayedIndex));
        card.append(body, trigger);
        return card;
      });
      gallery.replaceChildren(...cards);
      if (location.hash) document.getElementById(location.hash.slice(1))?.scrollIntoView();
      const filters = $('#gallery-filters');
      for (const category of ['All', ...icons.keys()]) {
        const tab = node('button', 'directory-filter');
        tab.type = 'button';
        tab.setAttribute('aria-pressed', String(category === 'All'));
        tab.append(galleryBadge(category));
        tab.addEventListener('click', () => {
          for (const button of $$('.directory-filter[aria-pressed]', filters)) {
            button.setAttribute('aria-pressed', String(button === tab));
          }
          cards.forEach((card, i) => {
            card.hidden = category !== 'All' && events[i].category !== category;
            if (card.hidden) players.get(card)?.setVisible(false);
            else if (!observer) players.get(card)?.setVisible(true);
          });
        });
        filters.append(tab);
      }
      if (events.some(event => event.media?.length > 1)) {
        const toggle = node('button', 'directory-filter gallery-preview-toggle', 'Pause previews');
        toggle.type = 'button';
        toggle.hidden = motionPreference.matches;
        toggle.addEventListener('click', () => {
          previewsPaused = !previewsPaused;
          toggle.textContent = previewsPaused ? 'Resume previews' : 'Pause previews';
          refreshAll();
        });
        motionPreference.addEventListener('change', () => { toggle.hidden = motionPreference.matches; });
        filters.append(toggle);
      }
    }).catch(() => { gallery.textContent = 'Lab Life is temporarily unavailable.'; });
  }

  const visitorPanel = $('.visitor-stats');
  if (visitorPanel) {
    const status = $('.visitor-status', visitorPanel);
    const numbers = new Intl.NumberFormat('en');
    const dialog = $('details', visitorPanel);
    function displayCounts(result) {
      for (const key of ['total', 'today']) {
        if (!Number.isSafeInteger(result[key]) || result[key] < 0) throw new Error('Invalid visitor total');
        $('[data-visitors="' + key + '"]', visitorPanel).textContent = numbers.format(result[key]);
      }
      status.hidden = true;
    }

    async function configureVisitorStats() {
      const {endpoint} = await getData('visitor-settings.json');
      if (!endpoint) return;
      const url = new URL(endpoint);
      if (url.protocol !== 'https:') throw new Error('Visitor stats require HTTPS');

      let id;
      try {
        id = localStorage.getItem('cmlab-visitor-id') || crypto.randomUUID();
        localStorage.setItem('cmlab-visitor-id', id);
      } catch {
        id = null;
      }
      const path = page === '404' ? '/404.html'
        : location.pathname === '/' ? '/index.html' : location.pathname;
      const recordVisit = Boolean(id && location.origin === 'https://cmlab-korea.github.io');
      const request = recordVisit ? {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({id, path})
      } : {};
      const result = await fetch(url, request);
      if (!result.ok) throw new Error('Visitor statistics unavailable');
      displayCounts(await result.json());

      let detailsLoaded = false;
      dialog.addEventListener('toggle', async () => {
        if (!dialog.open || detailsLoaded) return;
        const detailsStatus = $('.visitor-detail-status', dialog);
        try {
          const response = await fetch(url);
          if (!response.ok) throw new Error('Visitor breakdown unavailable');
          const breakdown = await response.json();
          const countryNames = new Intl.DisplayNames(['en'], {type: 'region'});
          for (const [key, list] of [['countries', breakdown.countries], ['pages', breakdown.pages]]) {
            const rows = Array.isArray(list) ? list : [];
            const target = $('[data-visitor-breakdown="' + key + '"]', dialog);
            target.replaceChildren(...rows.map(row => {
              const label = key === 'countries' && /^[A-Z]{2}$/.test(row.label) ? countryNames.of(row.label) : row.label;
              const item = node('li');
              item.append(node('span', '', label), node('span', '', numbers.format(row.count)));
              return item;
            }));
            if (!rows.length) target.append(node('li', '', 'No visits recorded yet.'));
          }
          detailsStatus.hidden = true;
          detailsLoaded = true;
        } catch {
          detailsStatus.hidden = false;
          detailsStatus.textContent = 'Visitor breakdown is temporarily unavailable.';
        }
      });
    }

    configureVisitorStats().catch(() => { status.textContent = 'Visitor statistics are temporarily unavailable.'; });
  }

})();
