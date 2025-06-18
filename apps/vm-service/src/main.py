"""Simple FastAPI application for VM management."""
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading
import sys
import os

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from core.config import settings
from core.logging import setup_logging, get_logger
from api.health import create_health_router

logger = get_logger("app")


class VMServiceHandler(BaseHTTPRequestHandler):
    """HTTP request handler for VM service."""
    
    def __init__(self, *args, **kwargs):
        self.health_check, self.readiness_check, self.liveness_check = create_health_router()
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """Handle GET requests."""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        try:
            if path == "/":
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                response = {
                    "service": settings.api_title,
                    "version": settings.api_version,
                    "docs": "/docs",
                    "health": "/api/v1/health"
                }
                self.wfile.write(json.dumps(response).encode())
                
            elif path == "/api/v1/health":
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                response = self.health_check()
                self.wfile.write(json.dumps(response).encode())
                
            elif path == "/api/v1/health/ready":
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                response = self.readiness_check()
                self.wfile.write(json.dumps(response).encode())
                
            elif path == "/api/v1/health/live":
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                response = self.liveness_check()
                self.wfile.write(json.dumps(response).encode())
                
            else:
                self.send_response(404)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                response = {"error": "Not found", "path": path}
                self.wfile.write(json.dumps(response).encode())
                
        except Exception as e:
            logger.error(f"Error handling request: {e}")
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {"error": "Internal server error"}
            self.wfile.write(json.dumps(response).encode())

    def do_OPTIONS(self):
        """Handle CORS preflight requests."""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', ','.join(settings.cors_origins))
        self.send_header('Access-Control-Allow-Methods', ','.join(settings.cors_methods))
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.send_header('Access-Control-Allow-Credentials', 'true' if settings.cors_credentials else 'false')
        self.end_headers()

    def end_headers(self):
        """Add CORS headers to all responses."""
        self.send_header('Access-Control-Allow-Origin', ','.join(settings.cors_origins))
        self.send_header('Access-Control-Allow-Credentials', 'true' if settings.cors_credentials else 'false')
        super().end_headers()

    def log_message(self, format, *args):
        """Override to use our logger."""
        logger.info(f"{self.client_address[0]} - {format % args}")


def create_app():
    """Create and configure the application."""
    setup_logging()
    logger.info("VM Management Service starting...")
    logger.info(f"Configuration loaded: {settings.api_title} v{settings.api_version}")
    return VMServiceHandler


def run_server():
    """Run the HTTP server."""
    handler_class = create_app()
    httpd = HTTPServer((settings.host, settings.port), handler_class)
    
    logger.info(f"🚀 VM Service running on http://{settings.host}:{settings.port}")
    logger.info(f"📋 Health check: http://{settings.host}:{settings.port}/api/v1/health")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down VM Management Service...")
        httpd.shutdown()


if __name__ == "__main__":
    run_server()