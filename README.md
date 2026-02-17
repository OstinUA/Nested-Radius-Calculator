# Nested Radius Calculator

![GitHub last commit](https://img.shields.io/github/last-commit/OstinUA/Nested-Radius-Calculator)
![GitHub language count](https://img.shields.io/github/languages/count/OstinUA/Nested-Radius-Calculator)
![GitHub top language](https://img.shields.io/github/languages/top/OstinUA/Nested-Radius-Calculator)

A tool for UI/UX designers and frontend developers. It allows for the instant calculation of the perfect corner radius for nested elements based on the outer radius and padding.

**[Open Demo](https://ostinua.github.io/Nested-Radius-Calculator/)**

---

## Overview

When creating interfaces, a common issue arises: if the same `border-radius` is set for both the outer container and the inner button, the corner spacing appears uneven. To make the interface look harmonious, the concentric radius rule must be applied.

This calculator automates the selection process, providing a visual preview and mathematically accurate data.

![Preview Screenshot](img_nested-radius-calculator.PNG)

## Key Features

* **Bidirectional Synchronization:** Changing any parameter (outer radius, padding, or inner radius) automatically recalculates the other values.
* **Real-time Visualization:** You can instantly see the result of applying `border-radius` and `padding` CSS properties.
* **Mathematical Precision:** Eliminates errors caused by visual estimation.
* **Multilingual:** Supports 10 interface languages.

## Mathematical Logic

The tool is based on the principle of concentric shapes. To ensure the border thickness (or padding) appears consistent on straight sections and in corners, the following formula is used:

$$R_{inner} = R_{outer} - Padding$$

Where:
* **R outer** — Parent container corner radius.
* **Padding** — Distance between the parent and child elements.
* **R inner** — Target radius of the child element.

> If $R_{outer} < Padding$, the inner radius must be 0; otherwise, the nested element will overflow the parent's curvature. The calculator accounts for this constraint.

## Language Support

The interface is translated into 10 languages for the convenience of users worldwide:

| Language | Menu Name |
| :--- | :--- |
| English | English |
| Russian | Русский |
| Ukrainian | Українська |
| Hindi | हिन्दी (Hindi) |
| Spanish | Español |
| Arabic | العربية (Arabic) |
| French | Français |
| Portuguese | Português |
| German | Deutsch |
| Indonesian | Bahasa Indonesia |

## Installation and Launch

The project does not require building, dependency installation, or Node.js. It is written in pure HTML, CSS, and JavaScript.

**Local Launch:**

1.  Clone the repository:
    ```bash
    git clone [https://github.com/OstinUA/Nested-Radius-Calculator.git](https://github.com/OstinUA/Nested-Radius-Calculator.git)
    ```
2.  Open the `index.html` file in any modern browser.

**GitHub Pages Deployment:**

1.  Go to repository **Settings**.
2.  Navigate to the **Pages** section.
3.  Under **Branch**, select `main` and click **Save**.
4.  In a few minutes, the site will be available at the link provided in the settings.

## Project Structure

* `index.html` — Markup and application structure.
* `style.css` — Styling, color variables, and responsiveness.
* `script.js` — Calculation logic and event handling.
* `translations.js` — Object containing language packages.

---

# Nested Radius Calculator

![GitHub last commit](https://img.shields.io/github/last-commit/OstinUA/Nested-Radius-Calculator)
![GitHub language count](https://img.shields.io/github/languages/count/OstinUA/Nested-Radius-Calculator)
![GitHub top language](https://img.shields.io/github/languages/top/OstinUA/Nested-Radius-Calculator)

Инструмент для UI/UX дизайнеров и фронтенд-разработчиков. Позволяет мгновенно рассчитать идеальный радиус скругления для вложенных элементов, основываясь на внешнем радиусе и отступах (padding).

**[Открыть демо](https://ostinua.github.io/Nested-Radius-Calculator/)**

---

## Обзор

При создании интерфейсов часто возникает проблема: если задать одинаковый `border-radius` для внешнего контейнера и внутренней кнопки, отступы в углах будут визуально казаться неравномерными. Чтобы интерфейс выглядел гармонично, необходимо использовать правило концентрических радиусов.

Этот калькулятор автоматизирует процесс подбора значений, предоставляя визуальное превью и математически точные данные.

![Preview Screenshot](img_nested-radius-calculator.PNG)

## Основные возможности

* **Двусторонняя синхронизация:** Изменение любого параметра (внешний радиус, отступ или внутренний радиус) автоматически пересчитывает остальные значения.
* **Визуализация в реальном времени:** Вы сразу видите результат применения CSS-свойств `border-radius` и `padding`.
* **Математическая точность:** Исключает ошибки визуального подбора "на глаз".
* **Мультиязычность:** Поддержка 10 языков интерфейса.

## Математическая логика

В основе работы лежит принцип концентричности фигур. Для того чтобы толщина рамки (или отступа) казалась одинаковой на прямых участках и в углах, используется формула:

$$R_{inner} = R_{outer} - Padding$$

Где:
* **R outer** — Радиус скругления родительского контейнера.
* **Padding** — Расстояние между родительским и дочерним элементом.
* **R inner** — Искомый радиус дочернего элемента.

> Если $R_{outer} < Padding$, внутренний радиус должен быть равен 0, иначе вложенный элемент выйдет за пределы родительского скругления. Калькулятор учитывает это ограничение.

## Поддержка языков

Интерфейс переведен на 10 языков для удобства пользователей по всему миру:

| Язык | Название в меню |
| :--- | :--- |
| Английский | English |
| Русский | Русский |
| Украинский | Українська |
| Хинди | हिन्दी (Hindi) |
| Испанский | Español |
| Арабский | العربية (Arabic) |
| Французский | Français |
| Португальский | Português |
| Немецкий | Deutsch |
| Индонезийский | Bahasa Indonesia |

## Установка и запуск

Проект не требует сборки, установки зависимостей или использования Node.js. Он написан на чистом HTML, CSS и JavaScript.

**Локальный запуск:**

1.  Склонируйте репозиторий:
    ```bash
    git clone [https://github.com/OstinUA/Nested-Radius-Calculator.git](https://github.com/OstinUA/Nested-Radius-Calculator.git)
    ```
2.  Откройте файл `index.html` в любом современном браузере.

**Размещение на GitHub Pages:**

1.  Зайдите в настройки репозитория (Settings).
2.  Перейдите в раздел **Pages**.
3.  В пункте **Branch** выберите `main` и нажмите **Save**.
4.  Через несколько минут сайт будет доступен по ссылке, указанной в настройках.

## Структура проекта

* `index.html` — Разметка и структура приложения.
* `style.css` — Стилизация, цветовые переменные и адаптивность.
* `script.js` — Логика вычислений и обработка событий.
* `translations.js` — Объект с языковыми пакетами.

