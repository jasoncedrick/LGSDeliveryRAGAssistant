/* Website presentation only. GSAP/Lenis and React Bits attribution: THIRD_PARTY.md. */
(() => {
  'use strict';
  const reduce = matchMedia('(prefers-reduced-motion: reduce)');
  const desktop = matchMedia('(min-width: 761px) and (pointer: fine)');
  const toggle = document.getElementById('motion-toggle');
  let optedOut = false, lenis = null, context = null;
  try { optedOut = localStorage.getItem('eboss-motion-off') === 'true'; } catch (_) {}
  const enabled = () => !reduce.matches && !optedOut;

  // Adapted from React Bits FadeContent's GSAP reveal/cleanup pattern for this
  // buildless application. No hidden initial CSS, blur, text splitting or scrub.
  function reveal() {
    context?.revert(); context = null;
    if (!enabled() || !window.gsap) return;
    const view = document.querySelector('.view:not([hidden])');
    const targets = view?.querySelectorAll('.location, h1, .lead, .about-steps article');
    if (!targets?.length || document.body.classList.contains('chat-started') && view.id === 'view-ask') return;
    context = gsap.context(() => {
      gsap.fromTo(targets, {opacity: .72, y: 8}, {
        opacity: 1, y: 0, duration: .4, stagger: .045, ease: 'power2.out',
        clearProps: 'opacity,transform'
      });
    }, view);
  }

  function update() {
    const on = enabled();
    document.documentElement.dataset.motion = on ? 'on' : 'off';
    toggle.textContent = reduce.matches ? 'Reduced motion' : on ? 'Motion on' : 'Motion off';
    toggle.setAttribute('aria-pressed', String(on));
    toggle.disabled = reduce.matches;
    toggle.title = reduce.matches ? 'Following your device reduced-motion setting' : 'Turn decorative motion on or off';
    if (!on) { context?.revert(); context = null; }
    // Native scrolling for chat, forms, touch devices and reduced motion.
    // Lenis gently smooths desktop wheel scrolling on information pages only.
    const informationPage = ['#sources', '#about'].includes(location.hash);
    const smooth = on && desktop.matches && informationPage && !document.hidden && window.Lenis;
    if (smooth && !lenis) lenis = new Lenis({autoRaf: true, duration: .65,
      smoothWheel: true, syncTouch: false, anchors: false,
      prevent: node => !!node.closest('textarea, select, details, [data-lenis-prevent]')});
    if (!smooth && lenis) { lenis.destroy(); lenis = null; }
    document.documentElement.dataset.smoothScroll = lenis ? 'on' : 'off';
  }
  toggle.addEventListener('click', () => {
    optedOut = !optedOut;
    try { localStorage.setItem('eboss-motion-off', String(optedOut)); } catch (_) {}
    update();
  });
  reduce.addEventListener('change', update);
  desktop.addEventListener('change', update);
  document.addEventListener('visibilitychange', update);
  window.addEventListener('hashchange', () => { update(); reveal(); });
  window.addEventListener('pagehide', () => { lenis?.destroy(); lenis = null; context?.revert(); });
  window.addEventListener('pageshow', update);
  update(); reveal();
})();
