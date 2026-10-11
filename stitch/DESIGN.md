---
name: Clarity Audio Intelligence
colors:
  surface: '#f7f9fe'
  surface-dim: '#d8dadf'
  surface-bright: '#f7f9fe'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f1f4f9'
  surface-container: '#eceef3'
  surface-container-high: '#e6e8ed'
  surface-container-highest: '#e0e2e7'
  on-surface: '#181c20'
  on-surface-variant: '#444654'
  inverse-surface: '#2d3135'
  inverse-on-surface: '#eff1f6'
  outline: '#747685'
  outline-variant: '#c4c5d6'
  surface-tint: '#3453ca'
  primary: '#2547be'
  on-primary: '#ffffff'
  primary-container: '#4361d8'
  on-primary-container: '#ebecff'
  inverse-primary: '#b8c4ff'
  secondary: '#4f5e84'
  on-secondary: '#ffffff'
  secondary-container: '#c2d1fe'
  on-secondary-container: '#4a5980'
  tertiary: '#005e55'
  on-tertiary: '#ffffff'
  tertiary-container: '#00796e'
  on-tertiary-container: '#9dfff1'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#dde1ff'
  primary-fixed-dim: '#b8c4ff'
  on-primary-fixed: '#001355'
  on-primary-fixed-variant: '#1139b2'
  secondary-fixed: '#dae2ff'
  secondary-fixed-dim: '#b7c6f2'
  on-secondary-fixed: '#081a3d'
  on-secondary-fixed-variant: '#37466b'
  tertiary-fixed: '#80f6e6'
  tertiary-fixed-dim: '#61d9ca'
  on-tertiary-fixed: '#00201c'
  on-tertiary-fixed-variant: '#005049'
  background: '#f7f9fe'
  on-background: '#181c20'
  surface-variant: '#e0e2e7'
typography:
  display:
    fontFamily: Be Vietnam Pro
    fontSize: 36px
    fontWeight: '700'
    lineHeight: 44px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Be Vietnam Pro
    fontSize: 28px
    fontWeight: '700'
    lineHeight: 36px
    letterSpacing: -0.015em
  headline-lg-mobile:
    fontFamily: Be Vietnam Pro
    fontSize: 24px
    fontWeight: '700'
    lineHeight: 32px
    letterSpacing: -0.01em
  headline-md:
    fontFamily: Be Vietnam Pro
    fontSize: 22px
    fontWeight: '600'
    lineHeight: 30px
    letterSpacing: -0.01em
  headline-sm:
    fontFamily: Be Vietnam Pro
    fontSize: 18px
    fontWeight: '600'
    lineHeight: 26px
  body-lg:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-sm:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  label-lg:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '600'
    lineHeight: 20px
    letterSpacing: 0.01em
  label-md:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
    letterSpacing: 0.02em
  label-sm:
    fontFamily: Inter
    fontSize: 11px
    fontWeight: '600'
    lineHeight: 14px
    letterSpacing: 0.04em
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  gutter: 1.5rem
  gutter-mobile: 1rem
  margin: 2rem
  margin-mobile: 1rem
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 1rem
  space-lg: 1.5rem
  space-xl: 2rem
---

## Brand & Style

This design system drives a speech emotion recognition application tailored for Vietnamese linguistic nuances. The brand ethos prioritizes clinical precision, acoustic transparency, and human empathy without visual distraction. The aesthetic rejects decorative clutter—eschewing all gradients, blurs, and glassmorphism—in favor of a disciplined, flat, content-first presentation.

### Visual Style
- **Pure Flat Modernism**: Every visual boundary is defined by crisp solid colors, calibrated structural borders, and controlled contrast ratios.
- **Acoustic Clarity**: High informational density balanced by ample breathing room, prioritizing waveform legibility, emotion distribution charts, and real-time inference telemetry.
- **Tone**: Analytical, reassuring, and culturally attuned, projecting technical reliability without visual coldness.

## Colors

The palette operates under a strict **60/30/10 spatial ratio** and an absolute prohibition against pure black, charcoal, or near-black values. All contrast is derived from deep navy blues and structural cool slates. Gradients, frosted surfaces, and ambient color blurs are forbidden; all surfaces are pure, flat solid fills.

### Palette Architecture

#### Neutrals (60% Surface Area)
- **Canvas Background**: `#F4F6FB`
- **Surface / Cards**: `#FFFFFF`
- **Surface Alternate**: `#EEF1F8`
- **Border / Structural Lines**: `#DCE2F0`

#### Primary System (30% Interactive Weight)
- **Primary Blue**: `#4361D8` (Interactive defaults, active states, key focus)
- **Primary Hover**: `#3047B0` (Pressed and hover interactions)
- **Primary Tint**: `#E8EDFC` (Subtle selection badges, active navigation items)
- **Primary Tint-2**: `#C5D1F7` (Secondary highlights, progress tracks)

#### Accents & Semantics (10% Focus Area)
- **Success / Teal**: `#1FA89A`
- **Warning / Ochre**: `#E9A23B`
- **Error / Crimson**: `#DC5A5A`

#### Text System (Zero Black)
- **Text Headings**: `#2F3E63` (Darkest permitted system token; foundational anchoring)
- **Text Body**: `#4A5878` (Readable, optimized contrast against white and light neutral)
- **Text Muted**: `#7A88A6` (Metadata, captions, inactive indicators)

#### Categorical Emotion Tokens (Strictly for Visualizations, Chips, and Indicators)
- **Trung tính (Neutral)**: `#8C9BB8`
- **Êm đềm (Calm / Serene)**: `#5BB5C6`
- **Vui vẻ (Happy)**: `#F2C14E`
- **Buồn bã (Sad)**: `#6A88D7`
- **Tức giận (Angry)**: `#E5675B`
- **Sợ hãi (Fearful)**: `#9A82C9`
- **Chán ghét (Disgust)**: `#84B26B`
- **Ngạc nhiên (Surprised)**: `#F29A52`

#### Discrete Acoustic Heatmap Scale (Stepped Only, No Interpolated Gradients)
- **Step 1 (Lowest)**: `#E8EDFC`
- **Step 2**: `#C5D1F7`
- **Step 3**: `#9DB1F0`
- **Step 4**: `#6F89E6`
- **Step 5 (Highest)**: `#4361D8`

## Typography

The typographic engine pairs **Be Vietnam Pro** for display and headline structures with **Inter** for analytical UI strings, tabular emotion metrics, and continuous body text. Be Vietnam Pro ensures optimal legibility and authentic balance for diacritics in Vietnamese speech transcripts, while Inter delivers dense data clarity without optical collision.

### Implementation Guidelines
- **Base Body Metric**: Desktop body defaults to 16px (`body-md`) with a line height of 24px (1.5).
- **Diacritic Clearance**: Headline levels use slightly expanded line heights relative to Latin norms to ensure Vietnamese stacked tone marks (dấu hỏi, dấu ngã, dấu nặng, dấu sắc, dấu huyền) never clip against container bounds.
- **Monospaced Data**: Numerical inference scores, confidence percentages, and audio timestamps use Inter’s tabular lining numerals (`tnum`) for vertical column alignment.

## Layout & Spacing

Layout geometry follows an exact **8px grid rhythm** (multiples of 0.5rem) across all axes.

### Architecture & Adaptability
- **Sidebar-App Shell**: Desktop applications anchor a permanent 260px vertical navigation sidebar on the left and an explicit 64px structural topbar.
- **Grid Structure**:
  - **Desktop (>= 1024px)**: 12-column fluid grid, 24px (`gutter`) gutters, 32px (`margin`) outer canvas margins.
  - **Tablet (768px - 1023px)**: 8-column grid, 16px gutters, 24px margins. Sidebar collapses to a fixed 72px rail.
  - **Mobile (< 768px)**: 4-column grid, 16px (`gutter-mobile`) gutters, 16px (`margin-mobile`) margins. Navigation collapses to a bottom utility bar or slide drawer.
- **Rhythm Rules**: Internal component spacing exclusively utilizes the standard tokens (`space-xs` = 4px, `space-sm` = 8px, `space-md` = 16px, `space-lg` = 24px, `space-xl` = 32px).

## Elevation & Depth

This system avoids heavy physical drop-shadows and disallows grey or black shadows entirely. Depth is achieved via **tonal surface separation** backed by low-opacity, blue-tinted ambient shadows.

### Elevation Tiers
- **Level 0 (Flat Ground)**: Canvas background `#F4F6FB`. Zero shadow.
- **Level 1 (Cards & Modules)**: Solid `#FFFFFF` fill, 1px solid border `#DCE2F0`, with `box-shadow: 0 2px 8px rgba(67, 97, 216, 0.04)`.
- **Level 2 (Dropdowns, Popovers, Floating Audio Controls)**: Solid `#FFFFFF` fill, 1px solid border `#DCE2F0`, with `box-shadow: 0 8px 24px rgba(67, 97, 216, 0.08)`.
- **Level 3 (Modal Overlays)**: Solid `#FFFFFF` fill, bordered by `#DCE2F0`, with `box-shadow: 0 16px 36px rgba(67, 97, 216, 0.12)`. Modal backdrops use solid `#2F3E63` at 40% opacity (no backdrop blur filters).

## Shapes

The geometric signature uses rounded rectilinear geometry to project an approachable yet controlled laboratory feel.

### Corner Radius Mapping
- **Cards, Panels, & Audio Waveform Windows**: Exactly `16px` (`rounded-lg`).
- **Interactive Controls (Buttons, Text Inputs, Dropdowns)**: Exactly `12px`.
- **Small Badges, Heatmap Cells, & Utility Indicators**: `6px` or `8px` (`rounded-sm`).
- **Emotion Tags & Audio Recording Trigger**: Fully pill-shaped (`9999px`) to distinguish categorical tags and tactile recording controls from data cards.

## Components

### 1. Navigation (Sidebar & Topbar)
- **Structural Bars**: Solid `#FFFFFF` background with a permanent 1px solid border in `#DCE2F0`.
- **Active Navigation Items**: Solid background `#E8EDFC` paired with `#4361D8` text and icon fill; no shadow.
- **Inactive Navigation Items**: Transparent background with `#4A5878` text, transitioning to `#EEF1F8` background on hover.

### 2. Buttons
- **Primary**: Solid `#4361D8` background, `#FFFFFF` text, radius 12px. Hover: solid `#3047B0`. Focus: 2px offset ring with `#C5D1F7`.
- **Secondary / Subtle**: Solid `#E8EDFC` background, `#4361D8` text. Hover: `#C5D1F7`.
- **Outline**: 1px solid `#DCE2F0`, `#2F3E63` text, `#FFFFFF` background. Hover: `#EEF1F8`.
- **Destructive**: Solid `#DC5A5A` background, `#FFFFFF` text.

### 3. Emotion Chips & Tags
- **Construction**: Pill-radius (`9999px`), 6px vertical padding, 12px horizontal padding.
- **Palette Logic**: Solid emotion accent dot (6px circle) paired with an 8% opacity emotion color background tint and `#2F3E63` typography. For high-prominence classification displays, use the solid emotion token as background with crisp `#FFFFFF` or `#2F3E63` text based on token luminance.

### 4. Audio Inputs & Visualizer Containers
- **Waveform Canvas**: Flat `#EEF1F8` background inside a 16px rounded card bordered with `#DCE2F0`.
- **Waveform Bars**: Inactive speech `#C5D1F7`; active playback `#4361D8`.
- **Spectrogram / Heatmap**: Stepped categorical cells utilizing the 5 discrete blue tokens (`#E8EDFC` to `#4361D8`) without linear gradients.

### 5. Input Fields & Selectors
- **Container**: Solid `#FFFFFF` background, radius 12px, border 1px solid `#DCE2F0`, typography `#2F3E63` (`body-md`).
- **Placeholder**: Solid `#7A88A6`.
- **Focus State**: Border color swaps to `#4361D8`, complemented by a clean, flat outer ring: `box-shadow: 0 0 0 3px #E8EDFC`.

### 6. Cards & Metric Tiles
- **Surface**: Solid `#FFFFFF`, radius 16px, border 1px solid `#DCE2F0`.
- **Shadow**: `0 2px 8px rgba(67, 97, 216, 0.04)`.
- **Header Structure**: Border-bottom 1px solid `#EEF1F8`, containing `#2F3E63` title and `#7A88A6` metadata.

### 7. Form Controls (Checkboxes & Radios)
- **Checkboxes**: 20px box, 6px radius, 1px solid `#DCE2F0`. Checked: solid `#4361D8` background with `#FFFFFF` check icon.
- **Radio Buttons**: 20px circle, 1px solid `#DCE2F0`. Selected: solid `#4361D8` outer border with a solid `#4361D8` internal circle separated by 2px white gap.