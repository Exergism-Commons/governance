const viewportFix = document.createElement('style');
viewportFix.id = 'viewport-width-fix';
viewportFix.textContent = `
  html, body {
    width: 100%;
    max-width: 100%;
    overflow-x: clip;
  }

  body,
  .site-header,
  main,
  footer,
  .hero,
  .statement,
  .section {
    width: 100%;
    max-width: 100%;
    min-width: 0;
  }

  .shell {
    width: 100% !important;
    max-width: 1180px;
    margin-inline: auto;
    padding-inline: 20px;
  }

  .hero-grid,
  .membership-grid,
  .machine-grid,
  .cla-grid,
  .cta-panel,
  .section-heading,
  .split-heading,
  .principles-grid,
  .decision-grid,
  .domain-grid,
  .status-panel,
  .membership-content {
    min-width: 0;
    max-width: 100%;
  }

  @media (max-width: 900px) {
    .shell {
      width: 100% !important;
      max-width: none;
      padding-inline: 15px;
    }
  }

  @media (max-width: 650px) {
    .shell {
      width: 100% !important;
      max-width: none;
      padding-inline: 12px;
    }

    .status-panel,
    .hero-copy,
    .hero-lead,
    .cta-panel {
      width: 100%;
      max-width: 100%;
    }
  }
`;
document.head.appendChild(viewportFix);

const navToggle = document.querySelector('.nav-toggle');
const nav = document.querySelector('#primary-nav');

if (navToggle && nav) {
  navToggle.addEventListener('click', () => {
    const open = nav.classList.toggle('is-open');
    navToggle.setAttribute('aria-expanded', String(open));
  });

  nav.addEventListener('click', event => {
    if (event.target instanceof HTMLAnchorElement) {
      nav.classList.remove('is-open');
      navToggle.setAttribute('aria-expanded', 'false');
    }
  });
}

for (const year of document.querySelectorAll('[data-year]')) {
  year.textContent = String(new Date().getFullYear());
}
