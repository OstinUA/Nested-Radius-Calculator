/**
 * Localization runtime for the nested corner radius calculator.
 *
 * Every dictionary is imported statically. The payloads are a few hundred bytes
 * each, the browser fetches them in parallel with the rest of the module graph,
 * and the UI never has to recover from a failed runtime lookup.
 *
 * `registry` is the single source of truth: the language picker, the lookup table
 * and the startup validation all derive from it, so supporting a new language is
 * one import plus one entry.
 */

import cs from './locales/cs.mjs';
import de from './locales/de.mjs';
import en from './locales/en.mjs';
import es from './locales/es.mjs';
import fr from './locales/fr.mjs';
import ja from './locales/ja.mjs';
import kk from './locales/kk.mjs';
import nl from './locales/nl.mjs';
import pl from './locales/pl.mjs';
import pt from './locales/pt.mjs';
import ru from './locales/ru.mjs';
import sv from './locales/sv.mjs';
import uk from './locales/uk.mjs';
import zh from './locales/zh.mjs';

/** Locale used whenever the requested language is unavailable. */
export const defaultLocale = 'en';

/** Declaration order drives the order of entries in the language picker. */
const registry = {
    en: { label: 'English', messages: en },
    zh: { label: '中文', messages: zh },
    es: { label: 'Español', messages: es },
    fr: { label: 'Français', messages: fr },
    pt: { label: 'Português', messages: pt },
    ru: { label: 'Русский', messages: ru },
    ja: { label: '日本語', messages: ja },
    de: { label: 'Deutsch', messages: de },
    uk: { label: 'Українська', messages: uk },
    pl: { label: 'Polski', messages: pl },
    nl: { label: 'Nederlands', messages: nl },
    kk: { label: 'Қазақша', messages: kk },
    sv: { label: 'Svenska', messages: sv },
    cs: { label: 'Čeština', messages: cs },
};

/** Locales exposed to the UI, in picker order. */
export const supportedLocales = Object.freeze(Object.keys(registry));

const messagesByLocale = Object.freeze(
    Object.fromEntries(
        Object.entries(registry).map(([locale, entry]) => [locale, Object.freeze(entry.messages)]),
    ),
);

/**
 * Verifies that every dictionary mirrors the reference locale.
 *
 * A translation contribution that drops or renames a key would otherwise render
 * as an empty label somewhere in the UI. Validating once at startup turns that
 * into an immediate, explicit failure that names the offending locale and keys.
 */
function assertDictionariesAreComplete(dictionaries) {
    const reference = dictionaries[defaultLocale];

    if (!reference) {
        throw new Error(`Default locale "${defaultLocale}" has no dictionary.`);
    }

    const referenceKeys = new Set(Object.keys(reference));

    for (const [locale, dictionary] of Object.entries(dictionaries)) {
        if (locale === defaultLocale) {
            continue;
        }

        const localeKeys = new Set(Object.keys(dictionary));
        const missing = [...referenceKeys].filter((key) => !localeKeys.has(key));
        const unexpected = [...localeKeys].filter((key) => !referenceKeys.has(key));
        const blank = [...localeKeys].filter((key) => {
            const value = dictionary[key];
            return typeof value !== 'string' || value.trim() === '';
        });

        if (missing.length > 0 || unexpected.length > 0 || blank.length > 0) {
            throw new Error(
                `Locale "${locale}" is out of sync with "${defaultLocale}". ` +
                    `Missing: ${missing.join(', ') || 'none'}. ` +
                    `Unexpected: ${unexpected.join(', ') || 'none'}. ` +
                    `Blank: ${blank.join(', ') || 'none'}.`,
            );
        }
    }
}

assertDictionariesAreComplete(messagesByLocale);

/** Reports whether `locale` is a language this build ships. */
export function isSupportedLocale(locale) {
    return typeof locale === 'string' && Object.hasOwn(registry, locale);
}

/**
 * Resolves the best supported locale for a BCP-47 tag list, as produced by
 * `navigator.languages`. Regional tags fall back to their base language, so
 * `pt-BR` matches `pt` and `de-AT` matches `de`.
 */
export function matchPreferredLocale(preferredLocales = []) {
    for (const tag of preferredLocales) {
        if (typeof tag !== 'string') {
            continue;
        }

        const normalised = tag.trim().toLowerCase();
        if (isSupportedLocale(normalised)) {
            return normalised;
        }

        const [baseLanguage] = normalised.split('-');
        if (isSupportedLocale(baseLanguage)) {
            return baseLanguage;
        }
    }

    return defaultLocale;
}

/** Language picker entries: the shipped locale codes paired with their labels. */
export function getLocaleOptions() {
    return supportedLocales.map((locale) => ({
        value: locale,
        label: registry[locale].label,
    }));
}

/**
 * Applies a locale to every `[data-i18n]` node in the document and returns the
 * locale that is actually active, which differs from `locale` when the request
 * is unsupported.
 */
export function setLanguage(locale) {
    const activeLocale = isSupportedLocale(locale) ? locale : defaultLocale;
    const activeMessages = messagesByLocale[activeLocale];
    const fallbackMessages = messagesByLocale[defaultLocale];

    document.documentElement.lang = activeLocale;

    // `textContent` is used deliberately: translation data is never parsed as
    // markup, so a dictionary entry can never introduce DOM nodes.
    for (const element of document.querySelectorAll('[data-i18n]')) {
        const key = element.dataset.i18n;
        const message = activeMessages[key] ?? fallbackMessages[key];

        if (message === undefined) {
            console.warn(`[i18n] No translation registered for key "${key}".`);
            continue;
        }

        element.textContent = message;
    }

    if (activeMessages.title) {
        document.title = activeMessages.title;
    }

    return activeLocale;
}
