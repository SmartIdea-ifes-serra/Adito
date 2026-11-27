'use strict';

const themeKey = 'adito-guia-tema';
const root = document.documentElement;
const systemTheme = window.matchMedia('(prefers-color-scheme: dark)');

function loadTheme() {
  try {
    const saved = localStorage.getItem(themeKey);
    if (saved === 'dark' || saved === 'light') return saved;
  } catch {
    // O guia também funciona nos navegadores que bloqueiam o armazenamento.
  }
  return systemTheme.matches ? 'dark' : 'light';
}

root.dataset.theme = loadTheme();

document.addEventListener('DOMContentLoaded', () => {
  const toggle = document.querySelector('.theme-toggle');
  const themeColor = document.querySelector('meta[name="theme-color"]');
  const brandAssets = document.querySelectorAll('[data-theme-brand]');
  let themeChosen = false;

  function applyTheme(theme) {
    root.dataset.theme = theme;
    const action = theme === 'dark' ? 'Ativar modo claro' : 'Ativar modo escuro';
    toggle.setAttribute('aria-label', action);
    toggle.title = action;
    themeColor.content = theme === 'dark' ? '#171B20' : '#173F35';

    brandAssets.forEach((asset) => {
      const attr = asset.tagName === 'LINK' ? 'href' : 'src';
      const url = asset.getAttribute(attr);
      asset.setAttribute(attr, url.replace(/adito-(light|dark)\.png$/, `adito-${theme}.png`));
    });
  }

  applyTheme(root.dataset.theme);
  toggle.hidden = false;
  toggle.addEventListener('click', () => {
    const next = root.dataset.theme === 'dark' ? 'light' : 'dark';
    themeChosen = true;
    applyTheme(next);
    try {
      localStorage.setItem(themeKey, next);
    } catch {
      // A escolha continua válida nesta página.
    }
  });
  systemTheme.addEventListener('change', () => {
    if (!themeChosen) applyTheme(loadTheme());
  });

  const search = document.querySelector('#search');
  const filters = [...document.querySelectorAll('.filter')];
  const questions = [...document.querySelectorAll('.question')];
  const feedback = document.querySelector('#feedback');
  const empty = document.querySelector('#empty');
  let activeFilter = 'todos';

  function normalize(text) {
    return text.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
  }

  function applyFilters() {
    const term = normalize(search.value.trim());
    let count = 0;
    for (const question of questions) {
      const matchesCategory = activeFilter === 'todos' || question.dataset.category === activeFilter;
      question.hidden = !matchesCategory || !normalize(question.textContent).includes(term);
      if (!question.hidden) count++;
    }
    empty.hidden = count !== 0;
    feedback.textContent = count === 1 ? '1 pergunta encontrada.' : `${count} perguntas encontradas.`;
  }

  search.addEventListener('input', applyFilters);
  filters.forEach((filter) => {
    filter.addEventListener('click', () => {
      activeFilter = filter.dataset.filter;
      filters.forEach((candidate) => {
        const selected = filter === candidate;
        candidate.classList.toggle('active', selected);
        candidate.setAttribute('aria-pressed', String(selected));
      });
      applyFilters();
    });
  });

  async function copyQuestion(text, button) {
    const label = 'Copiar';
    try {
      if (navigator.clipboard && window.isSecureContext) {
        await navigator.clipboard.writeText(text);
      } else {
        const field = document.createElement('textarea');
        field.value = text;
        field.style.position = 'fixed';
        field.style.opacity = '0';
        document.body.append(field);
        try {
          field.select();
          if (!document.execCommand('copy')) throw new Error('Falha ao copiar');
        } finally {
          field.remove();
          button.focus();
        }
      }
      button.textContent = 'Copiado!';
      feedback.textContent = 'Texto copiado.';
    } catch {
      button.textContent = 'Selecione o texto';
      feedback.textContent = 'Selecione o texto para copiar a pergunta.';
    }
    setTimeout(() => { button.textContent = label; }, 1700);
  }

  questions.forEach((question) => {
    const button = question.querySelector('.copy');
    const text = question.querySelector('p').textContent;
    button.setAttribute('aria-label', `Copiar pergunta: ${text}`);
    button.addEventListener('click', () => copyQuestion(text, button));
  });

  if ('IntersectionObserver' in window) {
    const links = [...document.querySelectorAll('.sidebar nav a')];
    const observer = new IntersectionObserver((entries) => {
      for (const entry of entries) {
        if (!entry.isIntersecting) continue;
        links.forEach((link) => {
          const current = link.hash === `#${entry.target.id}`;
          link.classList.toggle('active', current);
          if (current) link.setAttribute('aria-current', 'location');
          else link.removeAttribute('aria-current');
        });
      }
    }, { rootMargin: '-12% 0px -70% 0px' });
    document.querySelectorAll('main .section').forEach((section) => observer.observe(section));
  }
});
