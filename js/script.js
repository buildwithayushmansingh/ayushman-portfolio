// Bottom nav stays hidden — reveals when scrolling, or when the
// cursor/touch moves near the bottom edge of the screen.
const nav = document.getElementById('nav');
let mouseNearBottom = false;
let scrollActive = false;
let navHideTimer = null;
let profileMenuOpen = false; // set by the profile-menu script below

function updateNavVisibility() {
  nav.classList.toggle('nav-visible', mouseNearBottom || scrollActive || profileMenuOpen);
}

window.addEventListener('mousemove', e => {
  mouseNearBottom = (window.innerHeight - e.clientY) < 110;
  updateNavVisibility();
});

window.addEventListener('scroll', () => {
  scrollActive = true;
  updateNavVisibility();
  clearTimeout(navHideTimer);
  navHideTimer = setTimeout(() => {
    scrollActive = false;
    updateNavVisibility();
  }, 1200);
}, { passive: true });

window.addEventListener('touchstart', e => {
  mouseNearBottom = (window.innerHeight - e.touches[0].clientY) < 110;
  updateNavVisibility();
}, { passive: true });

// Mobile nav toggle
const navToggle = document.getElementById('navToggle');
const navLinks = document.getElementById('navLinks');
navToggle.addEventListener('click', () => navLinks.classList.toggle('open'));
navLinks.querySelectorAll('a').forEach(a =>
  a.addEventListener('click', () => navLinks.classList.remove('open'))
);

// Count-up stats, triggered once when the hero stats come into view
const counters = document.querySelectorAll('[data-count]');
let counted = false;

function runCounters() {
  if (counted) return;
  counted = true;
  counters.forEach(el => {
    const target = parseInt(el.getAttribute('data-count'), 10);
    const duration = 900;
    const start = performance.now();
    function tick(now) {
      const progress = Math.min((now - start) / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      el.textContent = Math.round(eased * target);
      if (progress < 1) requestAnimationFrame(tick);
    }
    requestAnimationFrame(tick);
  });
}

const statsSection = document.querySelector('.hero-stats');
if (statsSection) {
  const obs = new IntersectionObserver(
    entries => entries.forEach(e => { if (e.isIntersecting) runCounters(); }),
    { threshold: 0.4 }
  );
  obs.observe(statsSection);
}

// ---------- Certificate showcase: click a thumbnail to feature it ----------
(function () {
  const thumbs = document.querySelectorAll('.cert-thumb');
  if (!thumbs.length) return;

  const featuredImg = document.getElementById('certFeaturedImg');
  const featuredTitle = document.getElementById('certFeaturedTitle');
  const featuredIssuer = document.getElementById('certFeaturedIssuer');
  const featuredDesc = document.getElementById('certFeaturedDesc');
  const featuredTags = document.getElementById('certFeaturedTags');
  const featuredLink = document.getElementById('certFeaturedLink');

  thumbs.forEach(thumb => {
    thumb.addEventListener('click', () => {
      // swap the featured panel's content to match the clicked thumbnail
      featuredImg.src = thumb.dataset.image;
      featuredImg.alt = thumb.dataset.title;
      featuredTitle.textContent = thumb.dataset.title;
      featuredIssuer.textContent = thumb.dataset.issuer;
      featuredDesc.textContent = thumb.dataset.desc;
      featuredLink.href = thumb.dataset.image;

      featuredTags.innerHTML = '';
      thumb.dataset.tags.split(',').forEach(tag => {
        const span = document.createElement('span');
        span.className = 'tag';
        span.textContent = tag;
        featuredTags.appendChild(span);
      });

      thumbs.forEach(t => t.classList.remove('active'));
      thumb.classList.add('active');
    });
  });
})();

// ---------- Hero background: mouse + scroll parallax ----------
// Skipped entirely if the person has requested reduced motion.
(function () {
  const hero = document.getElementById('top');
  const bgLayer = document.getElementById('heroBgLayer');
  const heroOrbit = document.querySelector('.hero-orbit');
  if (!hero || !bgLayer) return;

  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (reduceMotion) return;

  const isTouchDevice = window.matchMedia('(pointer: coarse)').matches;

  let mouseX = 0, mouseY = 0;   // -1..1, normalized to hero center
  let smoothX = 0, smoothY = 0; // eased toward mouseX/Y each frame

  if (!isTouchDevice) {
    hero.addEventListener('mousemove', e => {
      const rect = hero.getBoundingClientRect();
      mouseX = ((e.clientX - rect.left) / rect.width - 0.5) * 2;
      mouseY = ((e.clientY - rect.top) / rect.height - 0.5) * 2;
    });
  }

  function tick() {
    smoothX += (mouseX - smoothX) * 0.04;
    smoothY += (mouseY - smoothY) * 0.04;

    // background drifts upward as the person scrolls past the hero
    const scrollShift = Math.min(window.scrollY, hero.offsetHeight) * 0.06;

    bgLayer.style.transform = `translate(${smoothX * 10}px, ${smoothY * 10 - scrollShift}px)`;
    if (heroOrbit) {
      // rings move less than the background text — creates a depth feel
      heroOrbit.style.transform = `translate(${smoothX * 4}px, ${smoothY * 4}px)`;
    }
    requestAnimationFrame(tick);
  }
  requestAnimationFrame(tick);
})();

// ---------- Custom cursor: scanner reticle + trailing dust ----------
// Skipped entirely on touch devices (no mouse to track)
const isTouch = window.matchMedia('(pointer: coarse)').matches;

if (!isTouch) {
  const cursor = document.getElementById('cursor');
  const cursorLabel = document.getElementById('cursorLabel');

  // crosshair follows the pointer instantly (feels precise, no lag)
  window.addEventListener('mousemove', e => {
    cursor.style.left = e.clientX + 'px';
    cursor.style.top = e.clientY + 'px';
  });

  // hide reticle when it leaves the window
  document.addEventListener('mouseleave', () => { cursor.style.opacity = '0'; });
  document.addEventListener('mouseenter', () => { cursor.style.opacity = '1'; });

  // brackets snap in + optional label on anything clickable
  const hoverTargets = 'a, button, .circuit-card, .orbit-card';
  document.querySelectorAll(hoverTargets).forEach(el => {
    el.addEventListener('mouseenter', () => {
      cursor.classList.add('active');
      const text = el.dataset.cursorText;
      if (text) {
        cursorLabel.textContent = text;
        cursorLabel.classList.add('visible');
      }
    });
    el.addEventListener('mouseleave', () => {
      cursor.classList.remove('active');
      cursorLabel.classList.remove('visible');
    });
  });

  // comet-style trailing dust: a small pool of squares that chase the pointer
  // with staggered easing, each one lagging slightly more than the last
  const TRAIL_LENGTH = 6;
  const trailDots = [];
  for (let i = 0; i < TRAIL_LENGTH; i++) {
    const dot = document.createElement('div');
    dot.className = 'cursor-trail';
    dot.style.opacity = String(0.5 - i * 0.07);
    dot.style.transform = `translate(-50%,-50%) rotate(45deg) scale(${1 - i * 0.12})`;
    document.body.appendChild(dot);
    trailDots.push({ el: dot, x: 0, y: 0 });
  }

  let pointerX = 0, pointerY = 0;
  window.addEventListener('mousemove', e => {
    pointerX = e.clientX;
    pointerY = e.clientY;
  });

  function animateTrail() {
    let targetX = pointerX;
    let targetY = pointerY;
    trailDots.forEach(dot => {
      dot.x += (targetX - dot.x) * 0.35;
      dot.y += (targetY - dot.y) * 0.35;
      dot.el.style.left = dot.x + 'px';
      dot.el.style.top = dot.y + 'px';
      targetX = dot.x;
      targetY = dot.y;
    });
    requestAnimationFrame(animateTrail);
  }
  animateTrail();
}

// ---------- Interface sound ----------
// Small synthesized blips via Web Audio — no audio files needed.
// Off by default; the person turns it on with the speaker button.
(function () {
  const toggle = document.getElementById('soundToggle');
  if (!toggle) return;

  let audioCtx = null;
  let soundOn = localStorage.getItem('soundOn') === 'true';
  toggle.setAttribute('aria-pressed', String(soundOn));

  function getCtx() {
    if (!audioCtx) {
      audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    }
    return audioCtx;
  }

  function blip(freq, duration, volume) {
    if (!soundOn) return;
    const ctx = getCtx();
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.type = 'sine';
    osc.frequency.value = freq;
    gain.gain.setValueAtTime(volume * (window.siteVolume ?? 0.6), ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + duration);
    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.start();
    osc.stop(ctx.currentTime + duration);
  }

  toggle.addEventListener('click', () => {
    soundOn = !soundOn;
    localStorage.setItem('soundOn', String(soundOn));
    toggle.setAttribute('aria-pressed', String(soundOn));
    if (soundOn) blip(660, 0.12, 0.05); // confirmation tone when turning on
  });

  // subtle hover tick + slightly deeper click tone on interactive elements
  document.querySelectorAll('a, button').forEach(el => {
    el.addEventListener('mouseenter', () => blip(880, 0.05, 0.02));
    el.addEventListener('click', () => blip(520, 0.08, 0.035));
  });
})();

// ---------- Profile menu: theme switch + sound + volume ----------
(function () {
  const profileMenu = document.getElementById('profileMenu');
  const avatarBtn = document.getElementById('profileAvatarBtn');
  const themeButtons = document.querySelectorAll('.theme-swatch');
  const volumeSlider = document.getElementById('volumeSlider');
  if (!profileMenu || !avatarBtn) return;

  // open/close dropdown — keep the bottom nav forced visible while it's open,
  // otherwise it auto-hides the moment the cursor moves up toward the menu
  avatarBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    const isOpen = profileMenu.classList.toggle('open');
    avatarBtn.setAttribute('aria-expanded', String(isOpen));
    profileMenuOpen = isOpen;
    updateNavVisibility();
  });
  document.addEventListener('click', (e) => {
    if (!profileMenu.contains(e.target)) {
      profileMenu.classList.remove('open');
      avatarBtn.setAttribute('aria-expanded', 'false');
      profileMenuOpen = false;
      updateNavVisibility();
    }
  });

  // theme switching — 'cinematic' is the default, so it needs no data-theme attribute
  function applyTheme(theme) {
    if (theme === 'cinematic') {
      document.documentElement.removeAttribute('data-theme');
    } else {
      document.documentElement.setAttribute('data-theme', theme);
    }
    themeButtons.forEach(btn => {
      btn.classList.toggle('active', btn.dataset.theme === theme);
    });
    localStorage.setItem('siteTheme', theme);
  }

  const savedTheme = localStorage.getItem('siteTheme') || 'cinematic';
  applyTheme(savedTheme);

  themeButtons.forEach(btn => {
    btn.addEventListener('click', () => applyTheme(btn.dataset.theme));
  });

  // volume — read by blip() in the sound-toggle script above
  const savedVolume = localStorage.getItem('soundVolume');
  window.siteVolume = savedVolume !== null ? parseInt(savedVolume, 10) / 100 : 0.6;

  if (volumeSlider) {
    volumeSlider.value = Math.round(window.siteVolume * 100);
    volumeSlider.addEventListener('input', () => {
      window.siteVolume = volumeSlider.value / 100;
      localStorage.setItem('soundVolume', volumeSlider.value);
    });
  }
})();

// ---------- Scroll-reveal for section content ----------
(function () {
  const revealEls = document.querySelectorAll('.reveal-on-scroll');
  if (!revealEls.length) return;

  const obs = new IntersectionObserver(
    entries => entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('in-view');
        obs.unobserve(entry.target);
      }
    }),
    { threshold: 0.15, rootMargin: '0px 0px -60px 0px' }
  );
  revealEls.forEach(el => obs.observe(el));
})();

// ---------- Nav: highlight the link for the section currently in view ----------
(function () {
  const sections = document.querySelectorAll('section[id]');
  const navLinkEls = document.querySelectorAll('.nav-links a[href^="#"]');
  if (!sections.length || !navLinkEls.length) return;

  const linkFor = id => document.querySelector(`.nav-links a[href="#${id}"]`);

  const spy = new IntersectionObserver(
    entries => entries.forEach(entry => {
      const link = linkFor(entry.target.id);
      if (!link) return;
      if (entry.isIntersecting) {
        navLinkEls.forEach(a => a.classList.remove('active'));
        link.classList.add('active');
      }
    }),
    { rootMargin: '-45% 0px -45% 0px' }
  );
  sections.forEach(sec => spy.observe(sec));
})();