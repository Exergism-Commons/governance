const wordmarkStylesheet = document.createElement('link');
wordmarkStylesheet.rel = 'stylesheet';
wordmarkStylesheet.href = 'wordmark.css';
wordmarkStylesheet.dataset.commonsWordmark = '';
document.head.appendChild(wordmarkStylesheet);

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
  .membership-content,
  .class-table {
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

    .class-table {
      overflow: visible !important;
      border: 0 !important;
      border-radius: 0 !important;
      background: transparent !important;
    }

    .class-table table {
      display: block !important;
      width: 100% !important;
      min-width: 0 !important;
      border-collapse: separate !important;
    }

    .class-table thead {
      position: absolute !important;
      width: 1px !important;
      height: 1px !important;
      padding: 0 !important;
      margin: -1px !important;
      overflow: hidden !important;
      clip: rect(0, 0, 0, 0) !important;
      white-space: nowrap !important;
      border: 0 !important;
    }

    .class-table tbody {
      display: grid !important;
      width: 100% !important;
      gap: 12px;
    }

    .class-table tr {
      display: block !important;
      width: 100% !important;
      padding: 18px;
      border: 1px solid var(--line);
      border-radius: 16px;
      background: var(--bg);
    }

    .class-table td {
      display: block !important;
      width: 100% !important;
      max-width: 100% !important;
      padding: 0 !important;
      border: 0 !important;
      overflow-wrap: anywhere;
      word-break: normal;
      font-size: .94rem;
      line-height: 1.5;
    }

    .class-table td + td {
      margin-top: 14px;
      padding-top: 14px !important;
      border-top: 1px solid var(--line) !important;
    }

    .class-table td::before {
      content: attr(data-label);
      display: block;
      margin-bottom: 5px;
      color: var(--muted);
      font-size: .68rem;
      font-weight: 800;
      letter-spacing: .08em;
      text-transform: uppercase;
    }

    .class-table td:first-child {
      font-size: 1.08rem;
      font-weight: 800;
      line-height: 1.25;
    }

    .class-table td:first-child::before {
      display: none;
    }

    .class-table code {
      white-space: normal;
      overflow-wrap: anywhere;
      font-size: .84rem !important;
    }
  }
`;
document.head.appendChild(viewportFix);

for (const table of document.querySelectorAll('.class-table table')) {
  const headers = Array.from(table.querySelectorAll('thead th')).map(header => header.textContent.trim());
  for (const row of table.querySelectorAll('tbody tr')) {
    Array.from(row.children).forEach((cell, index) => {
      if (cell instanceof HTMLTableCellElement && headers[index]) {
        cell.dataset.label = headers[index];
      }
    });
  }
}

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
