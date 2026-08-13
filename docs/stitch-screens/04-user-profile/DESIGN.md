---
name: Eco-Conscious Professionalism
colors:
  surface: '#f9faf7'
  surface-dim: '#d9dad8'
  surface-bright: '#f9faf7'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f3f4f1'
  surface-container: '#edeeeb'
  surface-container-high: '#e7e8e6'
  surface-container-highest: '#e2e3e0'
  on-surface: '#191c1b'
  on-surface-variant: '#42493d'
  inverse-surface: '#2e312f'
  inverse-on-surface: '#f0f1ee'
  outline: '#72796c'
  outline-variant: '#c2c9b9'
  surface-tint: '#3c6926'
  primary: '#1c4807'
  on-primary: '#ffffff'
  primary-container: '#33601e'
  on-primary-container: '#a5d988'
  inverse-primary: '#a1d584'
  secondary: '#466736'
  on-secondary: '#ffffff'
  secondary-container: '#c6eeb0'
  on-secondary-container: '#4b6d3b'
  tertiary: '#735c00'
  on-tertiary: '#ffffff'
  tertiary-container: '#cea700'
  on-tertiary-container: '#4e3e00'
  error: '#B91C1C'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#bcf19e'
  primary-fixed-dim: '#a1d584'
  on-primary-fixed: '#072100'
  on-primary-fixed-variant: '#245110'
  secondary-fixed: '#c6eeb0'
  secondary-fixed-dim: '#abd196'
  on-secondary-fixed: '#062100'
  on-secondary-fixed-variant: '#2f4f20'
  tertiary-fixed: '#ffe085'
  tertiary-fixed-dim: '#efc100'
  on-tertiary-fixed: '#231b00'
  on-tertiary-fixed-variant: '#574500'
  background: '#f9faf7'
  on-background: '#191c1b'
  surface-variant: '#e2e3e0'
  leaf-green: '#5D8D3E'
  sage-green: '#759B71'
  surface-white: '#FFFFFF'
  text-main: '#1C3B0F'
  success: '#5D8D3E'
  warning: '#F8C900'
typography:
  display-lg:
    fontFamily: Hanken Grotesk
    fontSize: 48px
    fontWeight: '800'
    lineHeight: '1.1'
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Hanken Grotesk
    fontSize: 32px
    fontWeight: '700'
    lineHeight: '1.2'
  headline-lg-mobile:
    fontFamily: Hanken Grotesk
    fontSize: 24px
    fontWeight: '700'
    lineHeight: '1.2'
  headline-md:
    fontFamily: Hanken Grotesk
    fontSize: 24px
    fontWeight: '600'
    lineHeight: '1.3'
  body-lg:
    fontFamily: Hanken Grotesk
    fontSize: 18px
    fontWeight: '400'
    lineHeight: '1.6'
  body-md:
    fontFamily: Hanken Grotesk
    fontSize: 16px
    fontWeight: '400'
    lineHeight: '1.6'
  label-md:
    fontFamily: Hanken Grotesk
    fontSize: 14px
    fontWeight: '600'
    lineHeight: '1.2'
    letterSpacing: 0.05em
  label-sm:
    fontFamily: Hanken Grotesk
    fontSize: 12px
    fontWeight: '500'
    lineHeight: '1.2'
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  unit: 4px
  gutter: 24px
  margin-mobile: 16px
  margin-desktop: 64px
  stack-sm: 8px
  stack-md: 16px
  stack-lg: 32px
---

## Brand & Style

The design system is engineered for a multi-regional digital tourism platform that balances environmental stewardship with professional reliability. The brand personality is **authoritative yet organic**, targeting conscious travelers and institutional partners.

The design style utilizes **High-Contrast Minimalism** mixed with **Corporate Modern** elements. It relies on a heavy white-space strategy to maintain legibility across diverse regional content. Visual interest is generated through high-impact photography framed by structured, geometric containers. The aesthetic is clean and "breathable," avoiding clutter to ensure the user feels a sense of calm and clarity during the travel planning process.

## Colors

The palette is rooted in a "Forest-to-Sun" spectrum. 
- **Forest Green (#33601E)** serves as the primary driver for interaction, used for primary buttons and active states.
- **Deep Green (#1C3B0F)** provides the grounding for typography, ensuring AAA accessibility against the neutral background. 
- **Sun Yellow (#F8C900)** is used sparingly as a "high-velocity" accent for alerts, ratings, and critical highlights.
- **Neutral Backgrounds** should favor `#F7F8F5` for large surface areas to reduce eye strain, while `#FFFFFF` is reserved for elevated cards and input fields.

## Typography

This design system uses **Hanken Grotesk** across all levels to maintain a sharp, contemporary, and highly legible appearance. The typeface's geometric clarity supports the "professional" pillar of the brand.

**Hierarchy Rules:**
- **Headlines:** Use Deep Green (#1C3B0F). Display sizes should utilize tight letter-spacing for a "bold" editorial look.
- **Body Text:** Use a generous `1.6` line height to ensure readability for long-form regional guides.
- **Labels:** Uppercase styling is recommended for `label-md` when used in buttons or category chips to increase distinction.

## Layout & Spacing

The design system employs a **12-column Fluid Grid** for desktop and a **4-column grid** for mobile. 

**Spacing Rhythm:**
- A base unit of **4px** drives all spatial decisions.
- **Section Spacing:** Large vertical gaps (stack-lg) are encouraged between content blocks to maintain the "clean and professional" aesthetic.
- **Alignment:** All text-heavy containers should be left-aligned to reinforce the systematic, structured nature of the platform. 
- **Margins:** Desktop views use expansive 64px margins to create a "contained" feel for wide-screen users.

## Elevation & Depth

Hierarchy is established through **Tonal Layering** supplemented by **Ambient Shadows**.

1.  **Base Layer:** `#F7F8F5` (The canvas).
2.  **Raised Layer (Cards):** `#FFFFFF` with a very soft, diffused shadow (`0px 4px 20px rgba(28, 59, 15, 0.06)`). The shadow uses a Deep Green tint rather than pure black to maintain color harmony.
3.  **Interaction Layer:** Hover states on cards should slightly increase shadow spread and lift the element by 2px.
4.  **Flat Elements:** Borders (`1px solid #759B71`) are used for secondary inputs and ghost buttons instead of shadows to keep the UI from feeling overly "heavy."

## Shapes

The shape language is **Rounded (0.5rem base)**. This strike a balance between the organic nature of "Eco" and the precision of "Professional."

- **Cards & Primary Buttons:** 0.5rem (8px).
- **Input Fields:** 0.5rem (8px).
- **Chips/Status Indicators:** Full pill-shape (rounded-xl) to distinguish them from actionable buttons.
- **Imagery:** Large hero images should maintain sharp corners or very subtle 4px radii to retain a high-end, editorial feel.

## Components

### Buttons
- **Primary:** Solid Forest Green (#33601E) with White text. High contrast, bold weight.
- **Secondary (Ghost):** 1.5px border of Forest Green with Forest Green text. Clear, high-visibility affordance.
- **Tertiary:** No border, Deep Green text with an underline on hover.

### Cards
- Dynamic containers for destinations. Use a white background, soft ambient shadow, and a 1px Sage Green border at 20% opacity. 
- Titles within cards should always be Deep Green.

### Input Fields
- Use a white background and a 1px Sage Green border. 
- Focus state: Border changes to Forest Green with a 2px outer "glow" of 10% opacity Forest Green.

### Status Indicators (Success/Warning)
- **Positive indicators:** Use Leaf Green (#5D8D3E).
- **Alerts/Prices:** Use Sun Yellow (#F8C900) for text or background accents to draw immediate attention.

### Lists & Navigation
- Navigation items should use `label-md` typography.
- Active states in lists are marked by a vertical 4px bar of Forest Green on the left edge.