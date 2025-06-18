# Rollo Site
Private Website project for portfolio and management stuff

## Overview
A modern, secure Angular website built with Node.js for showcasing portfolios and providing management tools. This project follows security best practices and provides a clean, professional interface.

## Technology Stack
- **Frontend**: Angular 20+
- **Runtime**: Node.js 20.19.2
- **Package Manager**: npm
- **Styling**: SCSS
- **Language**: TypeScript
- **Build System**: Angular CLI with esbuild

## Prerequisites
- Node.js 20.19.2 or later
- npm 10.8.2 or later
- Angular CLI 20+ (installed globally)

## Project Structure
```
rollo_site/
├── .angular/                 # Angular cache (generated)
├── .github/                  # GitHub workflows and templates
├── .vscode/                  # VS Code configuration
├── dist/                     # Build output (generated)
├── node_modules/             # Dependencies (generated)
├── public/                   # Static assets
│   └── favicon.ico
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
│   └── styles.scss           # Global styles
├── .editorconfig             # Editor configuration
├── .gitignore                # Git ignore rules
├── angular.json              # Angular workspace config
├── package.json              # Dependencies and scripts
├── package-lock.json         # Dependency lock file
├── README.md                 # This file
├── tsconfig.app.json         # TypeScript config for app
├── tsconfig.json             # Main TypeScript config
└── tsconfig.spec.json        # TypeScript config for tests
```

## Getting Started

### Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/darkstormgames/rollo_site.git
   cd rollo_site
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

### Development
Start the development server:
```bash
npm start
# or
ng serve
```

The application will be available at `http://localhost:4200/`

For external access (useful in containers or remote development):
```bash
npm run serve
# or
ng serve --host 0.0.0.0 --port 4200
```

### Building
Build the project for production:
```bash
npm run build
# or
ng build
```

The build artifacts will be stored in the `dist/rollo_site/` directory.

### Testing
Run unit tests:
```bash
npm test
# or
ng test
```

### Linting
Check code quality:
```bash
ng lint
```

## Available Scripts
- `npm start` - Start development server
- `npm run build` - Build for production
- `npm run watch` - Build and watch for changes
- `npm test` - Run unit tests
- `npm run serve` - Start dev server with external access

## Security Features
This project implements several security best practices:

### Content Security Policy (CSP)
- Restrictive CSP headers in `index.html`
- Protection against XSS attacks
- Limited script and style sources

### HTTP Security Headers
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Referrer-Policy: strict-origin-when-cross-origin`

### Development Security
- TypeScript for type safety
- Angular's built-in security features
- Secure routing configuration

## Folder Structure Details

### `/src/app/pages/`
Contains all page components:
- **Home**: Landing page with hero section and features
- **About**: Information about the platform and technology
- **Portfolio**: Showcase area for projects (placeholder)
- **Contact**: Contact information and forms (placeholder)

### `/src/app/`
Main application files:
- `app.ts` - Root component with navigation and layout
- `app.routes.ts` - Routing configuration
- `app.config.ts` - Application configuration
- `app.scss` - Navigation and layout styles

### `/src/`
- `index.html` - Main HTML template with security headers
- `main.ts` - Application bootstrap
- `styles.scss` - Global styles and utilities

## Styling Architecture
- **Global Styles**: Base styles, typography, utilities in `styles.scss`
- **Component Styles**: Scoped styles for each component
- **SCSS Features**: Variables, mixins, and nested selectors
- **Responsive Design**: Mobile-first approach with breakpoints

## Deployment Considerations
1. **Build Optimization**: Production builds are optimized and minified
2. **Security**: CSP headers and security meta tags included
3. **SEO**: Proper meta tags and semantic HTML structure
4. **Performance**: Tree-shaking and lazy loading ready

## Contributing
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## Browser Support
- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## License
ISC License - see package.json for details

## Version History
- v1.0.0 - Initial Angular project setup with security features and basic pages
