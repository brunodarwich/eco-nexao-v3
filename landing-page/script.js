/**
 * ECOnexão — Script da Página de Apresentação
 * Motion Design, Showcase Interativo e Acessibilidade
 */

document.addEventListener('DOMContentLoaded', () => {
  document.documentElement.classList.add('js-ready');

  /* ==========================================================================
     1. Scroll Reveal com IntersectionObserver
     ========================================================================== */
  const revealElements = document.querySelectorAll('.reveal');

  if ('IntersectionObserver' in window) {
    const revealObserver = new IntersectionObserver((entries, observer) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('active');
          observer.unobserve(entry.target);
        }
      });
    }, {
      threshold: 0.12,
      rootMargin: '0px 0px -40px 0px'
    });

    revealElements.forEach(el => revealObserver.observe(el));
  } else {
    // Fallback para navegadores legados
    revealElements.forEach(el => el.classList.add('active'));
  }

  /* ==========================================================================
     2. Header Fixo com Efeito de Vidro Dinâmico no Scroll
     ========================================================================== */
  const siteHeader = document.getElementById('header');

  const handleHeaderScroll = () => {
    if (window.scrollY > 40) {
      siteHeader.classList.add('scrolled');
    } else {
      siteHeader.classList.remove('scrolled');
    }
  };

  window.addEventListener('scroll', handleHeaderScroll, { passive: true });
  handleHeaderScroll();

  /* ==========================================================================
     3. Menu Mobile Acessível (Toggle)
     ========================================================================== */
  const mobileToggle = document.getElementById('mobile-toggle');
  const mobileMenu = document.getElementById('mobile-menu');
  const mobileLinks = document.querySelectorAll('.mobile-nav-link');

  if (mobileToggle && mobileMenu) {
    const toggleMenu = () => {
      const isExpanded = mobileToggle.getAttribute('aria-expanded') === 'true';
      mobileToggle.setAttribute('aria-expanded', !isExpanded);
      mobileToggle.classList.toggle('active');
      mobileMenu.classList.toggle('active');
      mobileMenu.setAttribute('aria-hidden', isExpanded);
    };

    mobileToggle.addEventListener('click', toggleMenu);

    // Fechar menu mobile ao clicar em qualquer link
    mobileLinks.forEach(link => {
      link.addEventListener('click', () => {
        mobileToggle.setAttribute('aria-expanded', 'false');
        mobileToggle.classList.remove('active');
        mobileMenu.classList.remove('active');
        mobileMenu.setAttribute('aria-hidden', 'true');
      });
    });
  }

  /* ==========================================================================
     4. Showcase Interativo das Telas do App (Carrossel / Tabs)
     ========================================================================== */
  const tabButtons = Array.from(document.querySelectorAll('.tab-btn'));
  const showcaseImg = document.getElementById('showcase-img');
  const showcaseTitle = document.getElementById('showcase-title');
  const showcaseDesc = document.getElementById('showcase-desc');
  const showcaseBadge = document.getElementById('showcase-badge');
  const showcaseTag = document.getElementById('showcase-tag');
  const ctrlIndicator = document.getElementById('ctrl-indicator');
  const prevBtn = document.getElementById('prev-screen');
  const nextBtn = document.getElementById('next-screen');

  let currentScreenIndex = 0;

  // Mapa de telas e imagens reais
  const screensData = [
    {
      screen: '01-home',
      imgSrc: 'assets/screens/01-home.png',
      alt: 'Tela inicial do ECOnexão com rotas do Tapajós',
      title: 'Início & Descoberta Territorial',
      desc: 'Visão clara do destino no primeiro toque. Seleção rápida de regiões do Tapajós, rotas em destaque no pôr do sol e acesso direto aos trajetos salvos pelo viajante.',
      badge: 'Tela Inicial',
      tag: 'Navegação Simples'
    },
    {
      screen: '02-routes',
      imgSrc: 'assets/screens/02-routes.png',
      alt: 'Listagem de rotas e trilhas com altimetria e dificuldade',
      title: 'Rotas e Trilhas com Altimetria',
      desc: 'Cards dinâmicos com distância precisa em quilômetros, nível de esforço físico, estimativa de duração, tipo de terreno e visualização prévia da rota.',
      badge: 'Roteiros',
      tag: 'Mapeamento Real'
    },
    {
      screen: '03-map',
      imgSrc: 'assets/screens/03-map.png',
      alt: 'Mapa georreferenciado com pins de serviços e alertas territoriais',
      title: 'Mapa Interativo e Alertas Territoriais',
      desc: 'Navegação geográfica com pins categorizados ao longo da rota traçada. Alertas práticos sobre trechos de areia fofa, horários de travessia e marés fluviais.',
      badge: 'Mapa PostGIS',
      tag: 'Alertas de Terreno'
    },
    {
      screen: '05-catalog',
      imgSrc: 'assets/screens/05-catalog.png',
      alt: 'Catálogo de pousadas, restaurantes e barqueiros locais',
      title: 'Catálogo Contextual de Atores Locais',
      desc: 'A vitrine digital dos pequenos negócios. Segmentação por hospedagem, gastronomia ribeirinha, condutores de lancha, guias e artesanato tradicional.',
      badge: 'Comércio Justo',
      tag: 'Contato Direto'
    },
    {
      screen: '04-profile',
      imgSrc: 'assets/screens/04-profile.png',
      alt: 'Perfil do usuário com dados baixados para consulta offline',
      title: 'Perfil do Viajante e Modo Offline',
      desc: 'Armazenamento local inteligente. As rotas e telefones de emergência ficam disponíveis no celular mesmo quando você estiver em áreas sem sinal de operadora.',
      badge: 'Offline-First',
      tag: 'Segurança Garantida'
    },
    {
      screen: '06-accessibility',
      imgSrc: 'assets/screens/06-accessibility.png',
      alt: 'Recursos de alto contraste e acessibilidade nativa no app',
      title: 'Acessibilidade e Inclusão Nativa',
      desc: 'Alto contraste para uso sob luz solar intensa, fontes com proporção ajustável e textos alternativos detalhados em todos os pontos e mapas para leitores de tela.',
      badge: 'WCAG AAA',
      tag: 'Inclusão Total'
    }
  ];

  const updateShowcase = (index) => {
    if (index < 0 || index >= screensData.length) return;
    currentScreenIndex = index;
    const data = screensData[index];

    // Atualiza classes ativas nos botões das tabs
    tabButtons.forEach((btn, i) => {
      const isActive = i === index;
      btn.classList.toggle('active', isActive);
      btn.setAttribute('aria-selected', isActive);
    });

    // Transição suave na imagem do celular
    if (showcaseImg) {
      showcaseImg.classList.add('switching');
      setTimeout(() => {
        showcaseImg.src = data.imgSrc;
        showcaseImg.alt = data.alt;
        showcaseImg.classList.remove('switching');
      }, 150);
    }

    // Atualiza os textos contextuais
    if (showcaseTitle) showcaseTitle.textContent = data.title;
    if (showcaseDesc) showcaseDesc.textContent = data.desc;
    if (showcaseBadge) showcaseBadge.textContent = data.badge;
    if (showcaseTag) showcaseTag.textContent = data.tag;
    if (ctrlIndicator) ctrlIndicator.textContent = `${index + 1} / ${screensData.length}`;
  };

  // Event Listeners nas tabs (Click e Teclado WAI-ARIA)
  tabButtons.forEach((btn, i) => {
    btn.addEventListener('click', () => {
      updateShowcase(i);
    });

    btn.addEventListener('keydown', (e) => {
      let targetIndex = null;
      if (e.key === 'ArrowRight' || e.key === 'ArrowDown') {
        e.preventDefault();
        targetIndex = (i + 1) % tabButtons.length;
      } else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
        e.preventDefault();
        targetIndex = (i - 1 + tabButtons.length) % tabButtons.length;
      } else if (e.key === 'Home') {
        e.preventDefault();
        targetIndex = 0;
      } else if (e.key === 'End') {
        e.preventDefault();
        targetIndex = tabButtons.length - 1;
      }

      if (targetIndex !== null) {
        tabButtons[targetIndex].focus();
        updateShowcase(targetIndex);
      }
    });
  });

  // Event Listeners nos botões Anterior e Próximo
  if (prevBtn) {
    prevBtn.addEventListener('click', () => {
      const newIndex = (currentScreenIndex - 1 + screensData.length) % screensData.length;
      updateShowcase(newIndex);
    });
  }

  if (nextBtn) {
    nextBtn.addEventListener('click', () => {
      const newIndex = (currentScreenIndex + 1) % screensData.length;
      updateShowcase(newIndex);
    });
  }

  /* ==========================================================================
     5. Formulário de Pitch e Demonstração
     ========================================================================== */
  const contactForm = document.getElementById('contact-form');
  const formFeedback = document.getElementById('form-feedback');
  const btnSubmitPitch = document.getElementById('btn-submit-pitch');

  if (contactForm) {
    contactForm.addEventListener('submit', (e) => {
      e.preventDefault();
      
      const name = document.getElementById('contact-name').value.trim();
      const email = document.getElementById('contact-email').value.trim();
      const role = document.getElementById('contact-role').value;
      const msg = document.getElementById('contact-msg').value.trim();

      if (!name || !email) {
        if (formFeedback) {
          formFeedback.textContent = 'Por favor, preencha seu nome e e-mail.';
          formFeedback.style.color = '#B91C1C';
        }
        return;
      }

      // Simulação de envio com feedback amigável
      btnSubmitPitch.disabled = true;
      btnSubmitPitch.innerHTML = '<span>Processando...</span>';

      setTimeout(() => {
        btnSubmitPitch.disabled = false;
        btnSubmitPitch.innerHTML = '<span>Solicitação Enviada!</span>';
        
        if (formFeedback) {
          formFeedback.className = 'form-feedback success';
          formFeedback.textContent = `Obrigado, ${name}! Recebemos sua mensagem e entraremos em contato pelo e-mail ${email} com a apresentação completa.`;
        }

        contactForm.reset();
      }, 800);
    });
  }

});
