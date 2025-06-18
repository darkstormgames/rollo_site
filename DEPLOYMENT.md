# Production Deployment Guide

## Prerequisites
- Node.js 20.19.2 or later
- npm 10.8.2 or later
- Angular CLI 20+

## Build for Production
```bash
npm run build
```

## Serve Static Files
After building, the `dist/rollo_site/` directory contains all static files needed for deployment.

### Option 1: Using Node.js HTTP Server
```bash
npm install -g http-server
cd dist/rollo_site
http-server -p 8080 -a 0.0.0.0
```

### Option 2: Using nginx
```nginx
server {
    listen 80;
    server_name your-domain.com;
    root /path/to/dist/rollo_site;
    index index.html;

    # Security headers
    add_header X-Frame-Options "DENY" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # Angular routing
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Cache static assets
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

### Option 3: Docker Deployment
```dockerfile
FROM nginx:alpine
COPY dist/rollo_site /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

## Security Checklist
- [x] CSP headers implemented
- [x] XSS protection enabled
- [x] Content type sniffing disabled
- [x] Frame options set to DENY
- [x] Referrer policy configured
- [ ] HTTPS/TLS configuration (deployment specific)
- [ ] Rate limiting (deployment specific)
- [ ] Web Application Firewall (deployment specific)

## Environment Variables
For production builds, consider setting:
- `NODE_ENV=production`
- `NG_BUILD_CACHE=false` (for clean builds)

## Performance Optimizations
- Bundle analysis: `ng build --stats-json && npx webpack-bundle-analyzer dist/rollo_site/stats.json`
- Enable gzip compression on server
- Configure proper cache headers
- Consider CDN for static assets