
let translations = {};
let currentLang = 'en';

export const getCurrentLanguage = () => currentLang;

async function fetchTranslations(lang) {
    try {
        const response = await fetch(`./locales/${lang}.json`);
        if (!response.ok) {
            console.error(`Could not load translation file for: ${lang}`);
            return {};
        }
        return await response.json();
    } catch (error) {
        console.error('Error fetching translations:', error);
        return {};
    }
}

function applyTranslations() {
    document.querySelectorAll('[data-i18n-key]').forEach(element => {
        const key = element.getAttribute('data-i18n-key');
        if (translations[key]) {
            if (element.tagName === 'BUTTON' && !element.querySelector('span')) {
                 element.textContent = translations[key];
            } else if (element.querySelector('span:not(.loader)')) {
                element.querySelector('span:not(.loader)').textContent = translations[key];
            }
            else {
                element.textContent = translations[key];
            }
        }
    });
}

export async function setLanguage(lang) {
    if (lang !== 'en' && lang !== 'hi') {
        lang = 'en';
    }
    currentLang = lang;
    translations = await fetchTranslations(lang);
    applyTranslations();
    localStorage.setItem('kisan-drishti-lang', lang);
    document.documentElement.lang = lang;

    document.dispatchEvent(new CustomEvent('language-changed'));
}

export function initI18n() {
    const savedLang = localStorage.getItem('kisan-drishti-lang') || 'en';
    const langSelector = document.getElementById('lang-selector');
    if(langSelector) {
        langSelector.value = savedLang;
        langSelector.addEventListener('change', (e) => setLanguage(e.target.value));
    }
    setLanguage(savedLang);
}