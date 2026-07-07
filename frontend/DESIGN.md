---
name: Vigilance Operations
colors:
  surface: '#051424'
  surface-dim: '#051424'
  surface-bright: '#2c3a4c'
  surface-container-lowest: '#010f1f'
  surface-container-low: '#0d1c2d'
  surface-container: '#122131'
  surface-container-high: '#1c2b3c'
  surface-container-highest: '#273647'
  on-surface: '#d4e4fa'
  on-surface-variant: '#c7c4d7'
  inverse-surface: '#d4e4fa'
  inverse-on-surface: '#233143'
  outline: '#908fa0'
  outline-variant: '#464554'
  surface-tint: '#c0c1ff'
  primary: '#c0c1ff'
  on-primary: '#1000a9'
  primary-container: '#8083ff'
  on-primary-container: '#0d0096'
  inverse-primary: '#494bd6'
  secondary: '#bec6e0'
  on-secondary: '#283044'
  secondary-container: '#3f465c'
  on-secondary-container: '#adb4ce'
  tertiary: '#bcc7de'
  on-tertiary: '#263143'
  tertiary-container: '#8691a7'
  on-tertiary-container: '#1f2a3c'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#e1e0ff'
  primary-fixed-dim: '#c0c1ff'
  on-primary-fixed: '#07006c'
  on-primary-fixed-variant: '#2f2ebe'
  secondary-fixed: '#dae2fd'
  secondary-fixed-dim: '#bec6e0'
  on-secondary-fixed: '#131b2e'
  on-secondary-fixed-variant: '#3f465c'
  tertiary-fixed: '#d8e3fb'
  tertiary-fixed-dim: '#bcc7de'
  on-tertiary-fixed: '#111c2d'
  on-tertiary-fixed-variant: '#3c475a'
  background: '#051424'
  on-background: '#d4e4fa'
  surface-variant: '#273647'
typography:
  headline-lg:
    fontFamily: Geist
    fontSize: 28px
    fontWeight: '600'
    lineHeight: 34px
    letterSpacing: -0.02em
  headline-md:
    fontFamily: Geist
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
    letterSpacing: -0.01em
  body-lg:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  label-mono:
    fontFamily: JetBrains Mono
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
    letterSpacing: 0.02em
  label-caps:
    fontFamily: Inter
    fontSize: 10px
    fontWeight: '700'
    lineHeight: 12px
    letterSpacing: 0.06em
  headline-lg-mobile:
    fontFamily: Geist
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 30px
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  unit: 4px
  container-padding: 16px
  stack-gap: 12px
  element-gap: 8px
  grid-gutter: 12px
---

## Brand & Style

The design system is engineered for high-stakes environments where split-second technical decisions are paramount. It adopts a **Technical Minimalism** aesthetic with **Glassmorphic** accents to evoke the feel of a modern Network Operations Center (NOC) condensed into a mobile form factor.

The brand personality is **Vigilant** and **Authoritative**. It prioritizes data density and legibility without sacrificing the premium feel of a high-end security tool. The UI should feel like a sophisticated instrument—precise, cold, and unwavering. Visual interest is generated through light-emitting elements (glows, vibrant semantic colors) contrasted against deep, structural shadows and semi-transparent layers.

## Colors

This design system utilizes a **Dark Mode** foundation to reduce eye strain during prolonged monitoring and to make high-contrast alerts immediately visible.

- **Primary (Electric Indigo):** Used for interactive states and primary focus areas. It should feel "energized" against the dark backdrop.
- **Surface Palette:** Deep charcoal and slate tones form the structural base, providing a "layered" depth.
- **Semantic System:** 
  - **Emerald (Healthy):** Used for verified secure states and successful heartbeats.
  - **Amber (Warning):** Used for anomalies, loop detection, or unusual traffic patterns.
  - **Ruby (Critical):** Reserved strictly for PII leaks, blocked intrusions, and active threats.
- **Neutral:** A range of cool grays used for metadata, inactive states, and secondary labels.

## Typography

The typographic scale is designed for **high-density data legibility**. 

- **Geist** is used for headlines to provide a sharp, technical "developer-tool" edge. 
- **Inter** handles the bulk of body content for its exceptional clarity on small screens. 
- **JetBrains Mono** is employed for all technical data, IP addresses, logs, and status codes to ensure character-level distinction.

Large headlines are condensed for mobile screens to maximize vertical real estate. Use `label-caps` for section headers and `label-mono` for any system-generated output or numerical metrics.

## Layout & Spacing

This design system uses a **4px baseline grid** to maintain technical precision. The layout is a **fluid-to-fixed hybrid** specifically optimized for mobile devices.

- **Margins:** A standard 16px lateral margin is maintained for all main containers.
- **Density:** Components are designed with "Tight" spacing (8px internal padding) to allow for more data points per scroll.
- **Responsiveness:** On larger mobile screens (tablets), the layout shifts to a 2-column grid for dashboards while keeping sidebar navigation fixed. 
- **Grouping:** Use 12px gaps between related cards and 24px gaps between distinct functional sections.

## Elevation & Depth

Hierarchy is established through **Glassmorphism** and **Tonal Layering** rather than traditional heavy shadows.

1.  **Base (Level 0):** The primary background (`#0F172A`).
2.  **Raised (Level 1):** Cards and containers use a slightly lighter fill (`#1E293B`) with a 1px inner stroke of 10% white to define edges.
3.  **Overlay (Level 2):** Modals and dropdowns use a semi-transparent background with a **20px Backdrop Blur**.
4.  **Accent Glows:** Critical alerts (Ruby) may use a subtle outer glow (4px blur, 20% opacity) to signify urgency and draw the eye immediately.

Avoid dropshadows that create "muddiness." Rely on thin, high-contrast borders (0.5pt to 1pt) to separate technical elements.

## Shapes

The shape language is **Structured and Precise**. 

- **Corners:** Use a consistent 4px (Soft) radius for most UI elements. This keeps the design feeling modern but "technical" and "instrument-like."
- **Interactive Elements:** Buttons and input fields share this 4px radius. 
- **Status Indicators:** Small dots and pips are perfectly circular to contrast against the rectangular grid.
- **Large Containers:** Can occasionally use 8px (`rounded-lg`) to differentiate major dashboard sections from individual data cells.

## Components

- **Buttons:** Primary buttons use a solid Electric Indigo fill with white text. Secondary buttons use a "Ghost" style with a 1px Indigo border.
- **Status Chips:** Small, pill-shaped indicators. They use a low-opacity background of the semantic color (e.g., 10% Emerald) with a solid-color label and a leading status dot.
- **Data Cards:** Utilize the Glassmorphic style—subtle background blur, 1px border, and high-density typography. Use JetBrains Mono for the primary metric value.
- **Input Fields:** Darker than the surface background with a 1px border that turns Electric Indigo on focus. Labels should use the `label-caps` style above the input.
- **Lists:** Data-heavy rows with thin dividers (`#1E293B`). Each row should include a leading semantic icon or status indicator.
- **Risk Gauges:** Circular or linear progress indicators using the semantic color scale (Emerald -> Amber -> Ruby) to show real-time threat levels.
- **Sparklines:** Compact, monochromatic line charts embedded in cards to show 24h trends without requiring a full chart view.