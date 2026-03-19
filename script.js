import { defaultLocale, localeLabels, setLanguage } from './i18n/index.mjs';

document.addEventListener('DOMContentLoaded', () => {
    const inputs = {
        outer: document.getElementById('outerInput'),
        outerRg: document.getElementById('outerRange'),
        pad: document.getElementById('paddingInput'),
        padRg: document.getElementById('paddingRange'),
        inner: document.getElementById('innerInput'),
        innerRg: document.getElementById('innerRange')
    };

    const preview = {
        outer: document.getElementById('previewOuter'),
        inner: document.getElementById('previewInner')
    };

    const langSelect = document.getElementById('langSelect');

    function populateLanguageOptions() {
        const optionsMarkup = Object.entries(localeLabels)
            .map(([locale, label]) => `<option value="${locale}">${label}</option>`)
            .join('');

        langSelect.innerHTML = optionsMarkup;
    }

    function render() {
        const outerVal = parseInt(inputs.outer.value, 10) || 0;
        const padVal = parseInt(inputs.pad.value, 10) || 0;
        const innerVal = parseInt(inputs.inner.value, 10) || 0;

        preview.outer.style.borderRadius = `${outerVal}px`;
        preview.inner.style.borderRadius = `${innerVal}px`;
        preview.outer.style.padding = `${padVal}px`;
    }

    function updateFromOuter(val) {
        const outer = parseInt(val, 10) || 0;
        const pad = parseInt(inputs.pad.value, 10) || 0;
        const inner = Math.max(0, outer - pad);

        inputs.outer.value = outer;
        inputs.outerRg.value = outer;
        inputs.inner.value = inner;
        inputs.innerRg.value = inner;

        render();
    }

    function updateFromPadding(val) {
        const pad = parseInt(val, 10) || 0;
        const outer = parseInt(inputs.outer.value, 10) || 0;
        const inner = Math.max(0, outer - pad);

        inputs.pad.value = pad;
        inputs.padRg.value = pad;
        inputs.inner.value = inner;
        inputs.innerRg.value = inner;

        render();
    }

    function updateFromInner(val) {
        const inner = parseInt(val, 10) || 0;
        const pad = parseInt(inputs.pad.value, 10) || 0;
        const outer = inner + pad;

        inputs.inner.value = inner;
        inputs.innerRg.value = inner;
        inputs.outer.value = outer;
        inputs.outerRg.value = outer;

        render();
    }

    populateLanguageOptions();
    langSelect.value = setLanguage(defaultLocale);

    inputs.outer.addEventListener('input', (e) => updateFromOuter(e.target.value));
    inputs.outerRg.addEventListener('input', (e) => updateFromOuter(e.target.value));

    inputs.pad.addEventListener('input', (e) => updateFromPadding(e.target.value));
    inputs.padRg.addEventListener('input', (e) => updateFromPadding(e.target.value));

    inputs.inner.addEventListener('input', (e) => updateFromInner(e.target.value));
    inputs.innerRg.addEventListener('input', (e) => updateFromInner(e.target.value));

    langSelect.addEventListener('change', (e) => {
        langSelect.value = setLanguage(e.target.value);
    });

    updateFromOuter(40);
});
