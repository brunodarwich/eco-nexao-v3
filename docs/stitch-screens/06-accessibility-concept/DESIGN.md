---
name: ECOnexão
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
  tertiary: '#1d4700'
  on-tertiary: '#ffffff'
  tertiary-container: '#336016'
  on-tertiary-container: '#a5d981'
  error: '#ba1a1a'
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
  tertiary-fixed: '#bcf296'
  tertiary-fixed-dim: '#a1d57d'
  on-tertiary-fixed: '#0a2100'
  on-tertiary-fixed-variant: '#255106'
  background: '#f9faf7'
  on-background: '#191c1b'
  surface-variant: '#e2e3e0'
typography:
  display-lg:
    fontFamily: Literata
    fontSize: 48px
    fontWeight: '700'
    lineHeight: 56px
    letterSpacing: -0.02em
  display-lg-mobile:
    fontFamily: Literata
    fontSize: 36px
    fontWeight: '700'
    lineHeight: 44px
    letterSpacing: -0.01em
  headline-md:
    fontFamily: Literata
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 40px
  headline-sm:
    fontFamily: Literata
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  body-lg:
    fontFamily: Manrope
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  body-md:
    fontFamily: Manrope
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  label-md:
    fontFamily: Manrope
    fontSize: 14px
    fontWeight: '600'
    lineHeight: 20px
    letterSpacing: 0.05em
  button:
    fontFamily: Manrope
    fontSize: 16px
    fontWeight: '700'
    lineHeight: 24px
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  base: 8px
  margin-mobile: 24px
  margin-desktop: 64px
  gutter: 16px
  stack-sm: 8px
  stack-md: 16px
  stack-lg: 32px
---

## Brand & Style
The design system for this product is rooted in the intersection of lush Amazonian nature and contemporary editorial sophistication. It serves travelers and locals in the Santarém region, prioritizing environmental immersion with uncompromising digital accessibility. 

The aesthetic is **Contemporary Editorial**, blending the organic warmth of the rainforest with the precision of a high-end travel journal. It utilizes heavy whitespace, oversized serif typography for narrative elements, and high-quality photography. The emotional response should be one of "Guided Adventure"—feeling both wild and safe, intuitive and deep. The UI is clean and systematic, yet feels alive through organic shapes and a grounding, earth-toned palette.

## Colors
The palette is a tonal study of the Amazonian canopy.

- **Primary (Forest):** Used for high-priority actions, active states, and navigation links. It represents the density of the woods.
- **Deep (Shadow):** Reserved for primary headings and high-contrast text. It ensures maximum readability and weight.
- **Leaf (Vibrant):** Used for positive reinforcement, progress indicators, and secondary illustrative elements.
- **Sage (Mist):** The primary utility color for soft borders, disabled states, and secondary surfaces to reduce visual noise.
- **Sun (Accent):** A high-visibility yellow used sparingly for alerts, rating stars, or critical points of interest on maps.
- **Surface:** The background remains ultra-clean (#F7F8F5) to allow photography and typography to breathe.

## Typography
The typography system relies on a dual-personality approach to achieve an editorial feel while maintaining rigorous accessibility standards.

- **Literata (Serif):** Used for titles, route names, and storytelling. It provides a human, organic touch that mirrors the historical and natural narrative of Santarém.
- **Manrope (Sans-serif):** Used for all functional UI elements, maps, data points, and body copy. It is chosen for its geometric clarity and excellent legibility at small sizes.
- **Hierarchy:** Ensure a minimum of 16px for body text to satisfy accessibility requirements for outdoor viewing (high glare). Use uppercase labels for metadata to distinguish it from narrative text.

## Layout & Spacing
The layout follows a strict **8-point grid** system to ensure harmony across all components. 

- **Margins:** A generous 24px side margin on mobile devices ensures that content does not feel cramped and provides a "safe zone" for thumb navigation.
- **Grid:** For web/tablet, use a 12-column fluid grid. For mobile, use a single-column stack with nested horizontal scrolling for "Category" chips or "Featured" cards.
- **Rhythm:** Vertical spacing between editorial sections should be aggressive (32px+) to maintain the contemporary "magazine" feel. Functional elements (inputs, list items) use tighter 8px or 16px gaps.

## Elevation & Depth
Depth is created through **Tonal Layering** and soft, environmental shadows rather than heavy skeuomorphism.

- **Level 0 (Base):** #F7F8F5 background.
- **Level 1 (Cards):** Pure white (#FFFFFF) with a 1px border in `brand-sage` at 40% opacity. 
- **Shadows:** Use "Ambient Shadows"—large blur radius (20px+), very low opacity (5-10%), and a slight green tint (#1C3B0F) in the shadow color to tie the element to the natural theme.
- **Interactive State:** On hover or press, the border weight does not change; instead, the shadow depth increases slightly to simulate the element "lifting" toward the user.

## Shapes
The shape language is "Organic Geometric." 

- **Standard Elements:** Buttons and input fields use a consistent 12px radius.
- **Large Containers:** Cards and image containers use a much more pronounced **18px to 24px** radius to evoke the softness of river stones and leaves.
- **Selection Indicators:** Use pill-shapes (full rounding) for tags and chips to differentiate them from actionable buttons.

## Components
- **Buttons:** Primary buttons must be `brand-forest` with white text, minimum 48px height for touch targets. Secondary buttons use `brand-sage` outlines.
- **Cards:** Travel cards should feature a top-heavy image ratio (3:2) with the title in `Literata` overlapping the image or immediately below it.
- **Maps:** Use a custom-styled map base that reduces urban saturation, emphasizing green areas and waterways. Map pins should use the `brand-sun` color for high contrast against the green base.
- **Inputs:** Use a soft background (#FFFFFF) with a `brand-sage` bottom border. Labels should stay visible (floating) to assist cognitive accessibility.
- **Chips/Filters:** Use `brand-leaf` for active filter states to provide a clear, positive feedback loop.
- **Accessibility Markers:** Inclusion of specific icons for "Wheelchair Accessible," "Audio Guide," or "Low Difficulty" should always be accompanied by text labels, never icons alone.