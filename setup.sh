#!/bin/bash

# Rollo Monorepo Setup Script
echo "Setting up Rollo Monorepo..."

# Install root dependencies
echo "Installing root dependencies..."
npm install

# Install app dependencies
echo "Installing dependencies for all apps..."
npm run install:all

echo "Setup complete!"
echo ""
echo "Available commands:"
echo "  npm run dev                  - Start main website"
echo "  npm run dev:rollo-site      - Start main website"
echo "  npm run dev:sso             - Start SSO service"
echo "  npm run build:all           - Build all applications"
echo "  npm run test:all            - Test all applications"
echo ""
echo "For development:"
echo "  cd apps/rollo-site && npm start    - Work on main website"
echo "  cd apps/sso && npm run dev         - Work on SSO service"