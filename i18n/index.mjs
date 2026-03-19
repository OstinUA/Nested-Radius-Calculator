import en from './locales/en.mjs';
import zh from './locales/zh.mjs';
import es from './locales/es.mjs';
import fr from './locales/fr.mjs';
import pt from './locales/pt.mjs';
import ru from './locales/ru.mjs';
import ja from './locales/ja.mjs';
import de from './locales/de.mjs';
import uk from './locales/uk.mjs';
import pl from './locales/pl.mjs';
import nl from './locales/nl.mjs';
import kk from './locales/kk.mjs';
import sv from './locales/sv.mjs';
import cs from './locales/cs.mjs';

export const defaultLocale = 'en';

export const localeLabels = {
    en: 'English',
    zh: '中文',
    es: 'Español',
    fr: 'Français',
    pt: 'Português',
    ru: 'Русский',
    ja: '日本語',
    de: 'Deutsch',
    uk: 'Українська',
    pl: 'Polski',
    nl: 'Nederlands',
    kk: 'Қазақша',
    sv: 'Svenska',
    cs: 'Čeština'
};

export const translations = {
    en,
    zh,
    es,
    fr,
    pt,
    ru,
    ja,
    de,
    uk,
    pl,
    nl,
    kk,
    sv,
    cs
};

function validateTranslations(sourceTranslations) {
    const [baseLocale, ...otherLocales] = Object.keys(sourceTranslations);
    const baseKeys = Object.keys(sourceTranslations[baseLocale]).sort();

    otherLocales.forEach((locale) => {
        const localeKeys = Object.keys(sourceTranslations[locale]).sort();
        const missingKeys = baseKeys.filter((key) => !localeKeys.includes(key));
        const extraKeys = localeKeys.filter((key) => !baseKeys.includes(key));

        if (missingKeys.length || extraKeys.length) {
            throw new Error(
                `Translation key mismatch for locale "${locale}". Missing: ${missingKeys.join(', ') || 'none'}. Extra: ${extraKeys.join(', ') || 'none'}.`
            );
        }
    });
}

validateTranslations(translations);

export function setLanguage(locale) {
    const activeLocale = translations[locale] ? locale : defaultLocale;

    document.documentElement.lang = activeLocale;
    document.querySelectorAll('[data-i18n]').forEach((element) => {
        const key = element.getAttribute('data-i18n');
        element.textContent = translations[activeLocale][key] ?? translations[defaultLocale][key] ?? '';
    });

    const title = translations[activeLocale].title ?? translations[defaultLocale].title;
    if (title) {
        document.title = title;
    }

    return activeLocale;
}
