/**
 * TRIMURTI / MSN-DV-001 Age-Inclusive Design Kit Client Logic (Annex C)
 *
 * Implements:
 * - Persistent Text Zoom (A / A+ / A++ -> 100% / 125% / 150%)
 * - Trilingual switching (English, मराठी, हिंदी)
 * - Web Speech API read-aloud (mr-IN, hi-IN, en-IN) with fallback
 * - Assisted mode banner toggle ("Someone is helping me")
 * - One-tap local state clearance ("Clear this phone")
 */

(function () {
  'use strict';

  // State keys
  const ZOOM_KEY = 'dv_text_zoom';
  const LANG_KEY = 'sn_language';
  const FALLBACK_LANG_KEY = 'dv_lang';
  const ASSISTED_KEY = 'dv_assisted_mode';

  // 1. Text Zoom Control
  function initTextZoom() {
    const savedZoom = localStorage.getItem(ZOOM_KEY) || '1';
    setZoom(parseFloat(savedZoom));

    const zoomButtons = document.querySelectorAll('.dv-btn-zoom');
    zoomButtons.forEach((btn) => {
      btn.addEventListener('click', () => {
        const factor = parseFloat(btn.dataset.zoom || '1');
        setZoom(factor);
        localStorage.setItem(ZOOM_KEY, factor.toString());
      });
    });
  }

  function setZoom(factor) {
    document.documentElement.style.setProperty('--dv-text-zoom', factor);
    const zoomButtons = document.querySelectorAll('.dv-btn-zoom');
    zoomButtons.forEach((btn) => {
      if (Math.abs(parseFloat(btn.dataset.zoom) - factor) < 0.05) {
        btn.classList.add('active');
        btn.setAttribute('aria-pressed', 'true');
      } else {
        btn.classList.remove('active');
        btn.setAttribute('aria-pressed', 'false');
      }
    });
  }

  // 2. Language Switcher
  function initLanguageSwitcher() {
    const savedLang = localStorage.getItem(LANG_KEY) || localStorage.getItem(FALLBACK_LANG_KEY) || 'mr'; // Marathi by default per Aaji motto
    setLanguage(savedLang);

    const langButtons = document.querySelectorAll('.dv-btn-lang');
    langButtons.forEach((btn) => {
      btn.addEventListener('click', () => {
        const lang = btn.dataset.lang || 'mr';
        setLanguage(lang);
        localStorage.setItem(LANG_KEY, lang);
        localStorage.setItem(FALLBACK_LANG_KEY, lang);
      });
    });

    window.addEventListener('storage', (e) => {
      if ((e.key === LANG_KEY || e.key === FALLBACK_LANG_KEY) && e.newValue) {
        setLanguage(e.newValue);
      }
    });
  }

  function setLanguage(lang) {
    document.documentElement.setAttribute('lang', lang);
    if (lang === 'mr' || lang === 'hi') {
      document.body.classList.add('lang-' + lang);
      document.body.classList.remove(lang === 'mr' ? 'lang-hi' : 'lang-mr');
    } else {
      document.body.classList.remove('lang-mr', 'lang-hi');
    }

    // Update trilingual DOM nodes
    const translatables = document.querySelectorAll('[data-i18n-en]');
    translatables.forEach((el) => {
      const text = el.getAttribute(`data-i18n-${lang}`) || el.getAttribute('data-i18n-en');
      if (text) {
        el.textContent = text;
      }
    });

    // Update active button state
    const langButtons = document.querySelectorAll('.dv-btn-lang');
    langButtons.forEach((btn) => {
      if (btn.dataset.lang === lang) {
        btn.classList.add('active');
        btn.setAttribute('aria-pressed', 'true');
      } else {
        btn.classList.remove('active');
        btn.setAttribute('aria-pressed', 'false');
      }
    });
  }

  // 3. Web Speech API Read-Aloud
  function initReadAloud() {
    const readButtons = document.querySelectorAll('.dv-read-aloud-btn');
    if (!('speechSynthesis' in window)) {
      readButtons.forEach((btn) => {
        btn.title = 'Read-aloud is not supported on this browser';
        btn.style.opacity = '0.6';
      });
      return;
    }

    readButtons.forEach((btn) => {
      btn.addEventListener('click', (e) => {
        e.preventDefault();
        window.speechSynthesis.cancel(); // Stop any ongoing speech

        const targetSelector = btn.dataset.readTarget;
        let textToRead = '';
        if (targetSelector) {
          const target = document.querySelector(targetSelector);
          if (target) textToRead = target.innerText;
        } else {
          // Read parent card or section
          const parent = btn.closest('.dv-card') || btn.parentElement;
          if (parent) textToRead = parent.innerText;
        }

        if (!textToRead) return;

        const currentLang = document.documentElement.getAttribute('lang') || 'mr';
        const utterance = new SpeechSynthesisUtterance(textToRead);
        
        let voiceLang = 'mr-IN';
        if (currentLang === 'hi') voiceLang = 'hi-IN';
        else if (currentLang === 'en') voiceLang = 'en-IN';
        utterance.lang = voiceLang;

        // Try finding matching voice
        const voices = window.speechSynthesis.getVoices();
        const matchedVoice = voices.find((v) => v.lang.startsWith(voiceLang) || v.lang.startsWith(currentLang));
        if (matchedVoice) {
          utterance.voice = matchedVoice;
        }

        utterance.rate = 0.9; // Slightly slower for elderly comprehension
        window.speechSynthesis.speak(utterance);
      });
    });
  }

  // 4. Assisted Mode Toggle
  function initAssistedMode() {
    const banner = document.getElementById('dv-assisted-banner');
    const toggleBtn = document.getElementById('dv-toggle-assisted');
    if (!banner || !toggleBtn) return;

    const isAssisted = localStorage.getItem(ASSISTED_KEY) === 'true';
    banner.style.display = isAssisted ? 'flex' : 'none';

    toggleBtn.addEventListener('click', () => {
      const active = banner.style.display !== 'none';
      const nextState = !active;
      banner.style.display = nextState ? 'flex' : 'none';
      localStorage.setItem(ASSISTED_KEY, nextState.toString());
    });
  }

  // 5. Clear This Device
  function initClearDevice() {
    const clearBtn = document.getElementById('dv-clear-device-btn');
    if (!clearBtn) return;

    clearBtn.addEventListener('click', () => {
      const lang = document.documentElement.getAttribute('lang') || 'mr';
      const confirmMsg =
        lang === 'mr'
          ? 'या फोनवरील सर्व माहिती कायमची पुसून टाकायची आहे का?'
          : lang === 'hi'
          ? 'क्या आप इस फ़ोन से अपनी सारी जानकारी हटाना चाहते हैं?'
          : 'Clear all your data from this phone?';

      if (window.confirm(confirmMsg)) {
        localStorage.clear();
        sessionStorage.clear();
        alert(
          lang === 'mr'
            ? 'माहिती सुरक्षितपणे हटवली आहे.'
            : lang === 'hi'
            ? 'जानकारी सुरक्षित रूप से हटा दी गई है।'
            : 'Your data has been wiped safely.'
        );
        window.location.reload();
      }
    });
  }

  // Initialize all components on DOMContentLoaded
  document.addEventListener('DOMContentLoaded', () => {
    initTextZoom();
    initLanguageSwitcher();
    initReadAloud();
    initAssistedMode();
    initClearDevice();
  });
})();
