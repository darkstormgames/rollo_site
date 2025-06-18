# Rollo Monorepo

This is a monorepo containing multiple Rollo applications and shared packages for better maintainability and code reuse across projects.

## Overview

The monorepo is structured to support multiple websites served over subdomains while sharing common styles and utilities. Each application is isolated for security and maintainability.

## Repository Structure

```
rollo-monorepo/
├── apps/                     # Individual applications
│   ├── rollo-site/          # Main website (Angular)
│   ├── sso/                 # SSO authentication service (Express.js)
│   └── vm-service/          # VM management service (Python/FastAPI)
├── packages/                # Shared packages
│   └── shared-styles/       # Common design system and styles
├── .github/                 # GitHub workflows and templates
├── .vscode/                 # VS Code configuration
├── DEPLOYMENT.md           # Deployment instructions
├── SSO_SETUP.md           # SSO setup guide
└── README.md              # This file
```

## Applications

### Rollo Site (`apps/rollo-site/`)
- **Technology**: Angular 20, TypeScript, SCSS
- **Purpose**: Main portfolio and management website
- **Features**: Responsive design, security headers, SEO optimization
- **Documentation**: See `apps/rollo-site/README.md`

### SSO Service (`apps/sso/`)
- **Technology**: Express.js, Node.js, MySQL
- **Purpose**: Secure Single Sign-On service for all applications
- **Features**: JWT authentication, multi-site support, user access levels
- **Documentation**: See `apps/sso/README.md`

### VM Service (`apps/vm-service/`)
- **Technology**: Python, FastAPI
- **Purpose**: Virtual machine management backend service
- **Features**: REST API, health checks, libvirt integration ready
- **Documentation**: See `apps/vm-service/README.md`

## Shared Packages

### Shared Styles (`packages/shared-styles/`)
- **Purpose**: Common design system and styles for all applications
- **Features**: Consistent branding, responsive utilities, theme support
- **Documentation**: See `packages/shared-styles/README.md`

## Quick Start

### Prerequisites
- Node.js 20+
- npm 10+
- Python 3.12+ (for VM service)
- MySQL 5.7+ (for SSO service)
- Angular CLI 20+ (for frontend development)

### Installation

Install all dependencies:
```bash
npm run install:all
```

Or install for specific apps:
```bash
npm run install:rollo-site
npm run install:sso
npm run install:vm-service
```

### Development

Start the main website:
```bash
npm run dev:rollo-site
# or
npm run dev
# or
npm start
```

Start the SSO service:
```bash
npm run dev:sso
```

Start the VM management service:
```bash
npm run dev:vm-service
```

### Building

Build all applications:
```bash
npm run build:all
```

Build specific applications:
```bash
npm run build:rollo-site
npm run build:sso
npm run build:vm-service
```

### Testing

Run all tests:
```bash
npm run test:all
```

Run tests for specific applications:
```bash
npm run test:rollo-site
npm run test:sso
npm run test:vm-service
```

## Available Scripts

From the root directory:

### Installation Scripts
- `npm run install:all` - Install dependencies for all apps
- `npm run install:rollo-site` - Install dependencies for main website
- `npm run install:sso` - Install dependencies for SSO service

### Development Scripts
- `npm run dev` or `npm start` - Start main website development server
- `npm run dev:rollo-site` - Start main website development server
- `npm run dev:sso` - Start SSO service development server

### Build Scripts
- `npm run build:all` - Build all applications for production
- `npm run build:rollo-site` - Build main website for production
- `npm run build:sso` - Build SSO service for production

### Test Scripts
- `npm run test:all` - Run tests for all applications
- `npm run test:rollo-site` - Run tests for main website
- `npm run test:sso` - Run tests for SSO service

## Architecture Benefits

### Security Isolation
- **SSO Service**: Completely isolated for maximum security
- **Separate Deployments**: Each app can be deployed independently
- **Environment Isolation**: Different configurations per app

### Code Sharing
- **Shared Styles**: Consistent design across all sites
- **Reusable Components**: Future shared components package
- **Common Utilities**: Shared business logic and helpers

### Scalability
- **Multi-Site Ready**: Architecture supports multiple subdomains
- **Independent Scaling**: Scale each service based on demand
- **Modular Development**: Teams can work on different apps independently

## Future Roadmap

- **Additional Sites**: Support for multiple subdomain sites
- **Shared Components**: React/Angular component library
- **API Gateway**: Centralized API management
- **Monitoring**: Centralized logging and monitoring
- **CI/CD**: Automated testing and deployment pipelines

## Contributing

Each application has its own development workflow. See individual README files in each app directory for specific contribution guidelines.

## Browser Support

Modern browsers supporting ES2020+ features. See individual app documentation for specific browser requirements.

## License

ISC License - see package.json files for details

## Version History

- **1.0.0** - Initial monorepo structure with rollo-site and SSO service