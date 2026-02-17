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

    function render() {
        const outerVal = parseInt(inputs.outer.value) || 0;
        const padVal = parseInt(inputs.pad.value) || 0;
        const innerVal = parseInt(inputs.inner.value) || 0;

        preview.outer.style.borderRadius = `${outerVal}px`;
        preview.inner.style.borderRadius = `${innerVal}px`;
        preview.outer.style.padding = `${padVal}px`;
    }

    function updateFromOuter(val) {
        let outer = parseInt(val) || 0;
        let pad = parseInt(inputs.pad.value) || 0;
        let inner = Math.max(0, outer - pad);

        inputs.outer.value = outer;
        inputs.outerRg.value = outer;
        inputs.inner.value = inner;
        inputs.innerRg.value = inner;
        
        render();
    }

    function updateFromPadding(val) {
        let pad = parseInt(val) || 0;
        let outer = parseInt(inputs.outer.value) || 0;
        let inner = Math.max(0, outer - pad);

        inputs.pad.value = pad;
        inputs.padRg.value = pad;
        inputs.inner.value = inner;
        inputs.innerRg.value = inner;
        
        render();
    }

    function updateFromInner(val) {
        let inner = parseInt(val) || 0;
        let pad = parseInt(inputs.pad.value) || 0;
        let outer = inner + pad;

        inputs.inner.value = inner;
        inputs.innerRg.value = inner;
        inputs.outer.value = outer;
        inputs.outerRg.value = outer;
        
        render();
    }

    inputs.outer.addEventListener('input', (e) => updateFromOuter(e.target.value));
    inputs.outerRg.addEventListener('input', (e) => updateFromOuter(e.target.value));

    inputs.pad.addEventListener('input', (e) => updateFromPadding(e.target.value));
    inputs.padRg.addEventListener('input', (e) => updateFromPadding(e.target.value));

    inputs.inner.addEventListener('input', (e) => updateFromInner(e.target.value));
    inputs.innerRg.addEventListener('input', (e) => updateFromInner(e.target.value));

    langSelect.addEventListener('change', (e) => setLanguage(e.target.value));

    setLanguage('en');
    updateFromOuter(40);
});
