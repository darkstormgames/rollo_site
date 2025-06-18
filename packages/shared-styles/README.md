# Shared Styles Package

This package contains the shared design system and styles for all Rollo applications.

## Structure

- `index.scss` - Main entry point with all base styles
- `components/` - Reusable component styles
- `utilities/` - Utility classes and mixins
- `themes/` - Theme variations for different sites

## Usage

Import in your application's main styles file:

```scss
@import '@rollo/shared-styles';

// Application-specific styles
// ...
```

## Design System

The shared styles provide:

- **Reset styles** - Consistent base styles across browsers
- **Typography** - Standardized heading and text styles
- **Colors** - Brand color palette
- **Buttons** - Consistent button components
- **Layout** - Container and utility classes
- **Responsive** - Mobile-first breakpoints

This enables consistent styling across multiple Rollo sites while allowing for site-specific customizations.