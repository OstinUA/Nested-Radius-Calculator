/**
 * UI controller for the nested corner radius calculator.
 *
 * The module owns one immutable snapshot of the three user-editable values and
 * renders it to the preview. Every control is bound to a single intent handler
 * (`outer`, `padding` or `inner`); the handler recomputes the other two values
 * from the geometry invariant, then writes the result to both the number field
 * and the slider of each parameter. Reading state back out of the DOM is
 * avoided on purpose: the DOM is treated as a rendering target, which keeps the
 * data flow one-directional and free of feedback loops.
 */

import {
    defaultLocale,
    getLocaleOptions,
    matchPreferredLocale,
    setLanguage,
} from './i18n/index.mjs';
import { innerRadiusFor, outerRadiusFor, toRadiusPixels } from './radius.mjs';

/** Locale the user picked last; survives a reload where storage is available. */
const LOCALE_STORAGE_KEY = 'nested-radius-calculator:locale';

const INITIAL_STATE = Object.freeze({ outer: 40, padding: 10 });

/**
 * Controls that share a parameter. Keeping the pair together removes the
 * duplicated wiring that a per-element listener would require and guarantees
 * the number field and the slider can never drift apart.
 */
const CONTROL_GROUPS = Object.freeze({
    outer: { input: 'outerInput', slider: 'outerRange' },
    padding: { input: 'paddingInput', slider: 'paddingRange' },
    inner: { input: 'innerInput', slider: 'innerRange' },
});

/** Maps a change in one parameter to the derived state. */
const DERIVATIONS = Object.freeze({
    outer: (value, state) => ({
        outer: value,
        padding: state.padding,
        inner: innerRadiusFor(value, state.padding),
    }),
    padding: (value, state) => ({
        outer: state.outer,
        padding: value,
        inner: innerRadiusFor(state.outer, value),
    }),
    inner: (value, state) => ({
        outer: outerRadiusFor(value, state.padding),
        padding: state.padding,
        inner: value,
    }),
});

/** Persisted preference access that degrades silently in restricted contexts. */
const localePreference = {
    read() {
        try {
            return window.localStorage.getItem(LOCALE_STORAGE_KEY);
        } catch {
            // Storage is unavailable in private or sandboxed browsing contexts.
            return null;
        }
    },
    write(locale) {
        try {
            window.localStorage.setItem(LOCALE_STORAGE_KEY, locale);
        } catch {
            // Failing to remember the preference is not a reason to break the UI.
        }
    },
};

function createElementLookup() {
    const elements = {};

    for (const [parameter, { input: inputId, slider: sliderId }] of Object.entries(CONTROL_GROUPS)) {
        const input = document.getElementById(inputId);
        const slider = document.getElementById(sliderId);

        if (!input || !slider) {
            throw new Error(`Missing markup for the "${parameter}" control group.`);
        }

        elements[parameter] = { input, slider };
    }

    return elements;
}

function main() {
    const controls = createElementLookup();
    const preview = {
        outer: document.getElementById('previewOuter'),
        inner: document.getElementById('previewInner'),
    };
    const languageSelect = document.getElementById('langSelect');

    if (!preview.outer || !preview.inner || !languageSelect) {
        throw new Error('The calculator markup is incomplete; aborting initialisation.');
    }

    let state = Object.freeze({
        ...INITIAL_STATE,
        inner: innerRadiusFor(INITIAL_STATE.outer, INITIAL_STATE.padding),
    });

    /**
     * Writes `state` to the DOM. Values are pixel integers, so a single style
     * write per affected property is enough — no rounding, no unit parsing.
     *
     * Fields are only assigned when they disagree with the state. Writing to a
     * focused field would move the caret to the end, and selection APIs are not
     * available on `input[type="number"]`, so avoiding the write is both the
     * cheapest and the only safe option while the user is typing.
     */
    function render() {
        for (const [parameter, { input, slider }] of Object.entries(controls)) {
            const value = String(state[parameter]);

            if (input.value !== value) {
                input.value = value;
            }
            slider.value = value;
        }

        const { style: outerStyle } = preview.outer;
        outerStyle.borderRadius = `${state.outer}px`;
        outerStyle.padding = `${state.padding}px`;
        preview.inner.style.borderRadius = `${state.inner}px`;
    }

    /**
     * Applies a user edit to one parameter and re-renders the derived state.
     *
     * Rendering is unconditional: even when the edit produces the state that is
     * already displayed, the edited field still has to snap back to the
     * normalised integer (for example "07" or "40.0").
     */
    function update(parameter, rawValue) {
        state = Object.freeze(DERIVATIONS[parameter](toRadiusPixels(rawValue), state));
        render();
    }

    function initialiseLanguage() {
        const options = getLocaleOptions().map(({ value, label }) => {
            const option = document.createElement('option');
            option.value = value;
            option.textContent = label;
            return option;
        });
        languageSelect.append(...options);

        const stored = localePreference.read();
        const initialLocale = stored ?? matchPreferredLocale(navigator.languages ?? [defaultLocale]);

        languageSelect.value = setLanguage(initialLocale);
    }

    for (const [parameter, { input, slider }] of Object.entries(controls)) {
        const handleInput = (event) => update(parameter, event.currentTarget.value);
        input.addEventListener('input', handleInput);
        slider.addEventListener('input', handleInput);
    }

    languageSelect.addEventListener('change', (event) => {
        const activeLocale = setLanguage(event.currentTarget.value);
        event.currentTarget.value = activeLocale;
        localePreference.write(activeLocale);
    });

    initialiseLanguage();
    render();
}

main();
