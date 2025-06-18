# Rollo Site - Main Website

The main Rollo website built with Angular 20. This serves as the primary portfolio and management interface.

## Technology Stack

- **Angular 20** - Frontend framework
- **TypeScript** - Type-safe JavaScript
- **SCSS** - Styling with shared design system
- **RxJS** - Reactive programming

## Project Structure

```
apps/rollo-site/
├── src/                      # Source code
│   ├── app/                  # Application code
│   │   ├── pages/            # Page components
│   │   │   ├── about/        # About page
│   │   │   ├── contact/      # Contact page
│   │   │   ├── home/         # Home page
│   │   │   └── portfolio/    # Portfolio page
│   │   ├── app.config.ts     # App configuration
│   │   ├── app.html          # Main app template
│   │   ├── app.routes.ts     # Routing configuration
│   │   ├── app.scss          # App-specific styles
│   │   ├── app.spec.ts       # App tests
│   │   └── app.ts            # Main app component
│   ├── index.html            # Main HTML file
│   ├── main.ts               # Application bootstrap
│   └── styles.scss           # Global styles (imports shared styles)
├── public/                   # Static assets
│   └── favicon.ico
├── angular.json              # Angular workspace config
├── tsconfig.app.json         # TypeScript config for app
├── tsconfig.json             # Main TypeScript config
├── tsconfig.spec.json        # TypeScript config for tests
└── package.json              # Dependencies and scripts
```

## Development

From the root directory:

```bash
# Install dependencies
npm install

# Start development server
npm run dev:rollo-site

# Build for production
npm run build:rollo-site

# Run tests
npm run test:rollo-site
```

From this directory:

```bash
# Install dependencies
npm install

# Start development server
npm start

# Build for production
npm run build

# Run tests
npm test
```

## Features

- **Responsive Design** - Mobile-first approach
- **Security Headers** - CSP, XSS protection, etc.
- **Performance Optimized** - Lazy loading, tree shaking
- **SEO Friendly** - Meta tags and structured data
- **Accessibility** - WCAG compliance

## Deployment

The application builds to `dist/rollo-site/` and can be served as static files.

See the main repository's DEPLOYMENT.md for deployment instructions.

## Shared Styles

This application uses the shared design system from `packages/shared-styles` to maintain consistency across all Rollo applications.