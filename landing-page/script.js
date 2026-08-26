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
     4. Showcase Interativo das Telas do App (Carrossel / Tabs / Autoplay)
     ========================================================================== */
  const tabButtons = Array.from(document.querySelectorAll('.tab-btn'));
  const showcaseImg = document.getElementById('showcase-img');
  const showcaseTitle = document.getElementById('showcase-title');
  const showcaseSubtitle = document.getElementById('showcase-subtitle');
  const showcaseDesc = document.getElementById('showcase-desc');
  const showcaseFeatures = document.getElementById('showcase-features');
  const showcaseBadge = document.getElementById('showcase-badge');
  const showcaseTag = document.getElementById('showcase-tag');
  const ctrlIndicator = document.getElementById('ctrl-indicator');
  const prevBtn = document.getElementById('prev-screen');
  const nextBtn = document.getElementById('next-screen');
  const btnAutoplay = document.getElementById('btn-autoplay');
  const autoplayIconPause = document.getElementById('autoplay-icon-pause');
  const autoplayIconPlay = document.getElementById('autoplay-icon-play');
  const autoplayLabel = document.getElementById('autoplay-label');
  const showcaseStage = document.getElementById('showcase-screen-panel');

  let currentScreenIndex = 0;
  let autoplayInterval = null;
  let isAutoplayActive = true;
  const AUTOPLAY_DELAY = 5000;

  // Mapa de dados sincronizado fielmente com copy_content.md
  const screensData = [
    {
      screen: '01-home',
      imgSrc: 'assets/screens/01-home.png',
      alt: 'Tela inicial do aplicativo ECOnexão exibindo regiões e rotas do Tapajós',
      title: '01. Início e Regiões',
      subtitle: 'Escolha seu ponto de partida no Tapajós.',
      desc: 'Alterne facilmente entre Santarém, Belterra e Alter do Chão para ver roteiros próximos, atrativos naturais e salvar caminhos para início rápido.',
      badge: 'Tela Inicial',
      tag: 'Navegação Simples',
      features: [
        'Seleção rápida de região',
        'Busca de locais e atrativos',
        'Atalhos para rotas recomendadas'
      ]
    },
    {
      screen: '02-routes',
      imgSrc: 'assets/screens/02-routes.png',
      alt: 'Catálogo de rotas e trilhas com distância e tipo de terreno no Tapajós',
      title: '02. Rotas e Trilhas Detalhadas',
      subtitle: 'Distância, tipo de solo e tempo estimado de percurso.',
      desc: 'Cada trajeto traz informações essenciais: quilometragem, esforço físico necessário, tipo de solo (areia de praia ou ramal de terra) e tempo médio a pé, de bicicleta ou de barco.',
      badge: 'Roteiros & Trilhas',
      tag: 'Perfil do Terreno',
      features: [
        'Filtro por nível de caminhada',
        'Pontos de saída (Porto, Rodoviária, Aeroporto)',
        'Resumo do terreno e relevo'
      ]
    },
    {
      screen: '03-map',
      imgSrc: 'assets/screens/03-map.png',
      alt: 'Mapa com pontos de interesse e avisos práticos',
      title: '03. Mapa do Trajeto e Avisos Práticos',
      subtitle: 'Pontos de apoio e dicas sobre o caminho.',
      desc: 'Visualize onde ficam quiosques, áreas de sombra, pontos de banho e atrativos naturais. A tela também mostra avisos úteis da comunidade, como trechos de areia fofa na estiagem ou áreas sem sinal.',
      badge: 'Mapa do Trajeto',
      tag: 'Avisos Práticos',
      features: [
        'Pontos de interesse e áreas de descanso',
        'Avisos sobre o terreno e condições do rio',
        'Visualização ampla em tela cheia'
      ]
    },
    {
      screen: '05-catalog',
      imgSrc: 'assets/screens/05-catalog.png',
      alt: 'Catálogo de pousadas familiares, restaurantes e barqueiros locais do Tapajós',
      title: '04. Comércio e Serviços da Comunidade',
      subtitle: 'Contato direto com quem recebe você no território.',
      desc: 'Encontre pousadas familiares, restaurantes caseiros, barqueiros, condutores locais e artesãos. Os cartões incluem número de WhatsApp, formas de pagamento aceitas e orientações de chegada.',
      badge: 'Contato Direto',
      tag: 'Sem Comissões',
      features: [
        'Filtros por tipo de serviço (Hospedagem, Alimentação, Barcos, Artesanato)',
        'Contato direto via WhatsApp e telefone',
        'Informações claras sobre o atendimento'
      ]
    },
    {
      screen: '04-profile',
      imgSrc: 'assets/screens/04-profile.png',
      alt: 'Painel do viajante com gestão de rotas e download para uso sem internet',
      title: '05. Gestão de Roteiros e Uso Offline',
      subtitle: 'Suas rotas guardadas para consultar sem internet.',
      desc: 'Guarde seus roteiros favoritos e baixe os mapas com antecedência. Assim, você consulta caminhos, contatos e pontos de interesse com autonomia mesmo em locais remotos.',
      badge: 'Modo Offline',
      tag: 'Uso Sem Internet',
      features: [
        'Download da rota em um toque',
        'Consumo econômico de bateria',
        'Sincronização ao reconectar'
      ]
    },
    {
      screen: '06-accessibility',
      imgSrc: 'assets/screens/06-accessibility.png',
      alt: 'Interface com alto contraste e informações de acessibilidade',
      title: '06. Acessibilidade e Clareza',
      subtitle: 'Informação transparente sobre a estrutura dos locais.',
      desc: 'O app indica de forma clara quais espaços possuem rampas, banheiros acessíveis e facilidade de acesso. A interface conta com alto contraste para leitura sob sol forte e suporte a leitores de tela.',
      badge: 'Acessibilidade',
      tag: 'Inclusão & Clareza',
      features: [
        'Informações práticas sobre acesso físico nos locais',
        'Texto legível com alto contraste para o sol',
        'Compatibilidade com leitores de tela'
      ]
    }
  ];

  const renderFeatures = (features) => {
    if (!showcaseFeatures) return;
    showcaseFeatures.innerHTML = '';
    features.forEach(feat => {
      const item = document.createElement('div');
      item.className = 'feature-pill-item';
      item.innerHTML = `
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" class="check-svg" aria-hidden="true">
          <polyline points="20 6 9 17 4 12"></polyline>
        </svg>
        <span>${feat}</span>
      `;
      showcaseFeatures.appendChild(item);
    });
  };

  const updateShowcase = (index) => {
    if (index < 0 || index >= screensData.length) return;
    currentScreenIndex = index;
    const data = screensData[index];

    // Atualiza classes ativas e atributos WAI-ARIA nas tabs
    tabButtons.forEach((btn, i) => {
      const isActive = i === index;
      btn.classList.toggle('active', isActive);
      btn.setAttribute('aria-selected', isActive ? 'true' : 'false');
      btn.setAttribute('tabindex', isActive ? '0' : '-1');
    });

    // Transição suave na imagem do smartphone
    if (showcaseImg) {
      showcaseImg.classList.add('switching');
      setTimeout(() => {
        showcaseImg.src = data.imgSrc;
        showcaseImg.alt = data.alt;
        showcaseImg.classList.remove('switching');
      }, 150);
    }

    // Atualiza os textos e badges
    if (showcaseTitle) showcaseTitle.textContent = data.title;
    if (showcaseSubtitle) showcaseSubtitle.textContent = data.subtitle;
    if (showcaseDesc) showcaseDesc.textContent = data.desc;
    if (showcaseBadge) showcaseBadge.textContent = data.badge;
    if (showcaseTag) showcaseTag.textContent = data.tag;
    if (ctrlIndicator) ctrlIndicator.textContent = `${index + 1} / ${screensData.length}`;

    // Renderiza lista de features dinâmicas
    renderFeatures(data.features);
  };

  // Autoplay Logic
  const startAutoplay = () => {
    stopAutoplay();
    autoplayInterval = setInterval(() => {
      const nextIndex = (currentScreenIndex + 1) % screensData.length;
      updateShowcase(nextIndex);
    }, AUTOPLAY_DELAY);
    isAutoplayActive = true;
    if (btnAutoplay) {
      btnAutoplay.classList.remove('paused');
      btnAutoplay.setAttribute('aria-pressed', 'true');
      if (autoplayIconPause) autoplayIconPause.style.display = 'block';
      if (autoplayIconPlay) autoplayIconPlay.style.display = 'none';
      if (autoplayLabel) autoplayLabel.textContent = 'Auto (5s)';
    }
  };

  const stopAutoplay = () => {
    if (autoplayInterval) {
      clearInterval(autoplayInterval);
      autoplayInterval = null;
    }
  };

  const pauseAutoplay = () => {
    stopAutoplay();
    isAutoplayActive = false;
    if (btnAutoplay) {
      btnAutoplay.classList.add('paused');
      btnAutoplay.setAttribute('aria-pressed', 'false');
      if (autoplayIconPause) autoplayIconPause.style.display = 'none';
      if (autoplayIconPlay) autoplayIconPlay.style.display = 'block';
      if (autoplayLabel) autoplayLabel.textContent = 'Pausado';
    }
  };

  if (btnAutoplay) {
    btnAutoplay.addEventListener('click', () => {
      if (isAutoplayActive) {
        pauseAutoplay();
      } else {
        startAutoplay();
      }
    });
  }

  // Pausa temporária durante interação do usuário (hover/focus)
  if (showcaseStage) {
    showcaseStage.addEventListener('mouseenter', () => {
      if (isAutoplayActive) stopAutoplay();
    });

    showcaseStage.addEventListener('mouseleave', () => {
      if (isAutoplayActive) startAutoplay();
    });

    showcaseStage.addEventListener('focusin', () => {
      if (isAutoplayActive) stopAutoplay();
    });

    showcaseStage.addEventListener('focusout', () => {
      if (isAutoplayActive) startAutoplay();
    });
  }

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

  // Inicializa o Showcase na tela inicial e inicia autoplay se usuário não preferir redução de movimento
  updateShowcase(0);

  const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (!prefersReducedMotion) {
    startAutoplay();
  } else {
    pauseAutoplay();
  }

  /* ==========================================================================
     5. Formulário de Pitch e Demonstração Institucional
     ========================================================================== */
  const contactForm = document.getElementById('contact-form');
  const formFeedback = document.getElementById('form-feedback');
  const btnSubmitPitch = document.getElementById('btn-submit-pitch');
  const nameInput = document.getElementById('contact-name');
  const orgInput = document.getElementById('contact-org');
  const emailInput = document.getElementById('contact-email');
  const interestInput = document.getElementById('contact-interest');
  const msgInput = document.getElementById('contact-msg');

  if (contactForm && btnSubmitPitch) {
    const nameError = document.getElementById('contact-name-error');
    const orgError = document.getElementById('contact-org-error');
    const emailError = document.getElementById('contact-email-error');
    const interestError = document.getElementById('contact-interest-error');

    // Validador de formato de e-mail RFC básico
    const isValidEmail = (email) => {
      const re = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
      return re.test(email);
    };

    const clearFieldErrors = () => {
      [nameInput, orgInput, emailInput, interestInput].forEach(input => {
        if (input) {
          input.setAttribute('aria-invalid', 'false');
        }
      });
      if (nameError) nameError.textContent = '';
      if (orgError) orgError.textContent = '';
      if (emailError) emailError.textContent = '';
      if (interestError) interestError.textContent = '';
      if (formFeedback) {
        formFeedback.textContent = '';
        formFeedback.className = 'form-feedback';
      }
    };

    // Limpeza de erros em digitação / interação
    [nameInput, orgInput, emailInput, interestInput].forEach(field => {
      if (field) {
        field.addEventListener('input', () => {
          field.setAttribute('aria-invalid', 'false');
          const errorSpan = document.getElementById(`${field.id}-error`);
          if (errorSpan) errorSpan.textContent = '';
        });
      }
    });

    let isSubmitting = false;

    contactForm.addEventListener('submit', (e) => {
      e.preventDefault();

      if (isSubmitting) return;

      clearFieldErrors();

      const nameVal = nameInput ? nameInput.value.trim() : '';
      const orgVal = orgInput ? orgInput.value.trim() : '';
      const emailVal = emailInput ? emailInput.value.trim() : '';
      const interestVal = interestInput ? interestInput.value : '';
      const msgVal = msgInput ? msgInput.value.trim() : '';

      let hasErrors = false;
      let firstInvalidElement = null;

      if (!nameVal) {
        hasErrors = true;
        if (nameInput) nameInput.setAttribute('aria-invalid', 'true');
        if (nameError) nameError.textContent = 'Informe seu nome completo.';
        if (!firstInvalidElement) firstInvalidElement = nameInput;
      }

      if (!orgVal) {
        hasErrors = true;
        if (orgInput) orgInput.setAttribute('aria-invalid', 'true');
        if (orgError) orgError.textContent = 'Informe sua instituição, comunidade ou atividade.';
        if (!firstInvalidElement) firstInvalidElement = orgInput;
      }

      if (!emailVal) {
        hasErrors = true;
        if (emailInput) emailInput.setAttribute('aria-invalid', 'true');
        if (emailError) emailError.textContent = 'Informe seu e-mail.';
        if (!firstInvalidElement) firstInvalidElement = emailInput;
      } else if (!isValidEmail(emailVal)) {
        hasErrors = true;
        if (emailInput) emailInput.setAttribute('aria-invalid', 'true');
        if (emailError) emailError.textContent = 'Insira um endereço de e-mail válido (ex: nome@dominio.com).';
        if (!firstInvalidElement) firstInvalidElement = emailInput;
      }

      if (!interestVal) {
        hasErrors = true;
        if (interestInput) interestInput.setAttribute('aria-invalid', 'true');
        if (interestError) interestError.textContent = 'Selecione uma opção de assunto.';
        if (!firstInvalidElement) firstInvalidElement = interestInput;
      }

      if (hasErrors) {
        if (formFeedback) {
          formFeedback.className = 'form-feedback error';
          formFeedback.textContent = 'Por favor, revise os campos obrigatórios assinalados acima.';
        }
        if (firstInvalidElement) {
          firstInvalidElement.focus();
        }
        return;
      }

      // Inicia estado de envio com proteção contra duplo clique
      isSubmitting = true;
      btnSubmitPitch.disabled = true;
      const btnText = btnSubmitPitch.querySelector('.btn-text');
      const btnSpinner = btnSubmitPitch.querySelector('.btn-spinner');
      const btnIcon = btnSubmitPitch.querySelector('.btn-icon-arrow');

      if (btnText) btnText.textContent = 'Enviando Mensagem...';
      if (btnSpinner) btnSpinner.style.display = 'inline-flex';
      if (btnIcon) btnIcon.style.display = 'none';

      // Simulação do envio com feedback amigável
      setTimeout(() => {
        isSubmitting = false;
        btnSubmitPitch.disabled = false;
        if (btnText) btnText.textContent = 'Mensagem Enviada!';
        if (btnSpinner) btnSpinner.style.display = 'none';
        if (btnIcon) btnIcon.style.display = 'inline';

        if (formFeedback) {
          formFeedback.className = 'form-feedback success';
          formFeedback.textContent = `Agradecemos pelo contato, ${nameVal}! Retornaremos em breve pelo e-mail ${emailVal}.`;
        }

        contactForm.reset();

        setTimeout(() => {
          if (btnText) btnText.textContent = 'Enviar Mensagem';
        }, 4000);
      }, 700);
    });
  }

});
