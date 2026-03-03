# Nested Radius Calculator

> Pixel-perfect nested border-radius math for UI engineers who hate eyeballing corners.

[![Build Status](https://img.shields.io/badge/build-static%20site-brightgreen?style=flat-square)](https://github.com/OstinUA/Nested-Radius-Calculator)
[![Version](https://img.shields.io/badge/version-1.0.0-blue?style=flat-square)](https://github.com/OstinUA/Nested-Radius-Calculator)
[![License: Apache 2.0](https://img.shields.io/badge/license-Apache%202.0-orange?style=flat-square)](LICENSE)
[![Coverage](https://img.shields.io/badge/coverage-manual-lightgrey?style=flat-square)](https://github.com/OstinUA/Nested-Radius-Calculator)

**Live demo:** [Open in browser](https://ostinua.github.io/Nested-Radius-Calculator/)

![Preview Screenshot](img_nested-radius-calculator.PNG)

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
- [Usage](#usage)
- [Configuration](#configuration)
- [License](#license)
- [Contacts](#contacts)

## Features

- Two-way sync between `outer radius`, `padding`, and `inner radius`.
- Real-time visual preview of nested corners.
- Formula-driven calculation using concentric radius logic.
- Guard rails for invalid geometry (`inner radius` is clamped at `0`).
- Fast, dependency-free runtime (no bundler, no build step).
- Built-in multilingual support via translation dictionary.

## Tech Stack

- `HTML5`
- `CSS3`
- `Vanilla JavaScript (ES6+)`
- `GitHub Pages` for hosting

## Project Structure

```text
Nested-Radius-Calculator/
├── index.html         # App shell and UI markup
├── style.css          # Styling and responsive layout
├── script.js          # Radius math + UI event wiring
├── translations.js    # i18n strings map
├── LICENSE            # Apache 2.0
└── README.md          # Project docs
```

## Getting Started

### Prerequisites

You only need a modern browser:

- `Chrome`, `Firefox`, `Safari`, or `Edge`
- `Git` (optional, only for cloning)

### Installation

```bash
# 1) Clone the repo
git clone https://github.com/OstinUA/Nested-Radius-Calculator.git

# 2) Move into the project folder
cd Nested-Radius-Calculator

# 3) Run locally by opening the HTML entrypoint
# Linux:
xdg-open index.html
# macOS:
open index.html
# Windows (PowerShell):
start index.html
```

## Usage

```bash
# Optional: start a tiny local server (better for consistent browser behavior)
python3 -m http.server 8080

# Then open:
# http://localhost:8080
```

```text
1) Set the outer radius of the parent container.
2) Set padding between parent and child.
3) Read the computed inner radius.
4) Copy values into CSS: border-radius + padding.
```

Core formula used by the calculator:

```text
innerRadius = max(outerRadius - padding, 0)
```

## Configuration

This project is intentionally zero-config:

- No `.env` required.
- No runtime flags.
- No external services.

To customize behavior, edit:

- `translations.js` for language packs.
- `style.css` for theming and layout tuning.
- `script.js` for calculation or UI logic.

## License

Distributed under the Apache 2.0 License. See `LICENSE` for full legal text.

## Contacts

## ❤️ Support the Project

If you find this tool useful, consider leaving a ⭐ on GitHub or supporting the author directly:

[![Patreon](https://img.shields.io/badge/Patreon-OstinFCT-f96854?style=flat-square&logo=patreon)](https://www.patreon.com/OstinFCT)
[![Ko-fi](https://img.shields.io/badge/Ko--fi-fctostin-29abe0?style=flat-square&logo=ko-fi)](https://ko-fi.com/fctostin)
[![Boosty](https://img.shields.io/badge/Boosty-Support-f15f2c?style=flat-square)](https://boosty.to/ostinfct)
[![YouTube](https://img.shields.io/badge/YouTube-FCT--Ostin-red?style=flat-square&logo=youtube)](https://www.youtube.com/@FCT-Ostin)
[![Telegram](https://img.shields.io/badge/Telegram-FCTostin-2ca5e0?style=flat-square&logo=telegram)](https://t.me/FCTostin)
