const translations = {
    en: {
        title: "Corner Radius Calculator",
        label_outer: "Outer Radius",
        label_padding: "Padding",
        label_inner: "Inner Radius",
        pill_outer: "Outer",
        pill_padding: "Padding",
        pill_inner: "Inner",
        footer: "Made for designers"
    },
    ru: {
        title: "Калькулятор скругления",
        label_outer: "Внешний радиус",
        label_padding: "Отступ (Padding)",
        label_inner: "Внутренний радиус",
        pill_outer: "Внешний",
        pill_padding: "Отступ",
        pill_inner: "Внутр.",
        footer: "Сделано для дизайнеров"
    },
    ua: {
        title: "Калькулятор заокруглення",
        label_outer: "Зовнішній радіус",
        label_padding: "Відступ (Padding)",
        label_inner: "Внутрішній радіус",
        pill_outer: "Зовн.",
        pill_padding: "Відступ",
        pill_inner: "Внутр.",
        footer: "Зроблено для дизайнерів"
    },
    hi: {
        title: "कोना त्रिज्या कैलकुलेटर",
        label_outer: "बाहरी त्रिज्या",
        label_padding: "पैडिंग",
        label_inner: "आंतरिक त्रिज्या",
        pill_outer: "बाहरी",
        pill_padding: "पैडिंग",
        pill_inner: "आंतरिक",
        footer: "डिजाइनरों के लिए बनाया गया"
    },
    es: {
        title: "Calculadora de Radio",
        label_outer: "Radio Exterior",
        label_padding: "Relleno (Padding)",
        label_inner: "Radio Interior",
        pill_outer: "Exterior",
        pill_padding: "Relleno",
        pill_inner: "Interior",
        footer: "Hecho para diseñadores"
    },
    ar: {
        title: "حاسبة نصف القطر",
        label_outer: "نصف القطر الخارجي",
        label_padding: "الحشوة (Padding)",
        label_inner: "نصف القطر الداخلي",
        pill_outer: "خارجي",
        pill_padding: "حشوة",
        pill_inner: "داخلي",
        footer: "صنع للمصممين"
    },
    fr: {
        title: "Calculateur de Rayon",
        label_outer: "Rayon Externe",
        label_padding: "Marge (Padding)",
        label_inner: "Rayon Interne",
        pill_outer: "Externe",
        pill_padding: "Marge",
        pill_inner: "Interne",
        footer: "Fait pour les designers"
    },
    pt: {
        title: "Calculadora de Raio",
        label_outer: "Raio Externo",
        label_padding: "Preenchimento",
        label_inner: "Raio Interno",
        pill_outer: "Externo",
        pill_padding: "Padding",
        pill_inner: "Interno",
        footer: "Feito para designers"
    },
    de: {
        title: "Eckenradius Rechner",
        label_outer: "Außenradius",
        label_padding: "Abstand (Padding)",
        label_inner: "Innenradius",
        pill_outer: "Außen",
        pill_padding: "Abstand",
        pill_inner: "Innen",
        footer: "Gemacht für Designer"
    },
    id: {
        title: "Kalkulator Radius",
        label_outer: "Radius Luar",
        label_padding: "Padding",
        label_inner: "Radius Dalam",
        pill_outer: "Luar",
        pill_padding: "Padding",
        pill_inner: "Dalam",
        footer: "Dibuat untuk desainer"
    }
};

function setLanguage(lang) {
    document.documentElement.lang = lang;
    document.querySelectorAll('[data-i18n]').forEach(element => {
        const key = element.getAttribute('data-i18n');
        if (translations[lang] && translations[lang][key]) {
            element.textContent = translations[lang][key];
        }
    });
}
