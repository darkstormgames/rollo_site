"""Main VM Agent Service."""

import asyncio
import signal
import sys
import time
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import schedule
import threading

from config import AgentConfig, load_config, validate_config, get_agent_id
from .api_client import APIClient
from .metrics import MetricsCollector
from .operations import VMOperations, VMOperationError


# Setup logging
def setup_logging(config: AgentConfig):
    """Setup logging configuration."""
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, config.log_level.upper()),
        format=log_format,
        handlers=[]
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter(log_format))
    logging.getLogger().addHandler(console_handler)
    
    # File handler if specified
    if config.log_file:
        try:
            file_handler = logging.FileHandler(config.log_file)
            file_handler.setFormatter(logging.Formatter(log_format))
            logging.getLogger().addHandler(file_handler)
        except Exception as e:
            logging.error(f"Failed to setup file logging: {e}")


class VMAgent:
    """Main VM Agent Service."""
    
    def __init__(self, config: AgentConfig):
        """Initialize the VM Agent."""
        self.config = config
        self.agent_id = get_agent_id()
        self.logger = logging.getLogger(f"vm_agent.{self.agent_id}")
        
        # Initialize components
        self.api_client = APIClient(config)
        self.metrics_collector = MetricsCollector(config.libvirt_uri)
        self.vm_operations = VMOperations(config.libvirt_uri)
        
        # Agent state
        self.running = False
        self.last_heartbeat = 0
        self.last_metrics_collection = 0
        self.registration_successful = False
        
        # Background tasks
        self._tasks = []
        self._scheduler_thread = None
        self._schedule_stop_event = threading.Event()
        
    async def start(self):
        """Start the VM Agent service."""
        self.logger.info(f"Starting VM Agent {self.agent_id}")
        
        # Validate configuration
        validation = validate_config(self.config)
        if not validation["valid"]:
            self.logger.error("Configuration validation failed:")
            for issue in validation["issues"]:
                self.logger.error(f"  - {issue}")
            return False
        
        if validation["warnings"]:
            for warning in validation["warnings"]:
                self.logger.warning(f"  - {warning}")
        
        # Test libvirt connection
        health = self.vm_operations.health_check()
        if health["status"] != "healthy":
            self.logger.error(f"Libvirt health check failed: {health.get('error', 'Unknown error')}")
            return False
        
        self.logger.info(f"Libvirt connection healthy: {health['hostname']}")
        
        # Auto-register if enabled
        if self.config.auto_register:
            if not await self._register():
                self.logger.error("Failed to register with backend")
                return False
        
        # Start background tasks
        self.running = True
        await self._start_background_tasks()
        
        self.logger.info("VM Agent started successfully")
        return True
    
    async def stop(self):
        """Stop the VM Agent service."""
        self.logger.info("Stopping VM Agent")
        
        self.running = False
        
        # Stop scheduler
        if self._scheduler_thread:
            self._schedule_stop_event.set()
            self._scheduler_thread.join(timeout=5)
        
        # Cancel tasks
        for task in self._tasks:
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        
        # Close connections
        try:
            self.api_client.close()
            self.metrics_collector.close()
            self.vm_operations.close()
        except Exception as e:
            self.logger.error(f"Error closing connections: {e}")
        
        self.logger.info("VM Agent stopped")
    
    async def _register(self) -> bool:
        """Register agent with backend."""
        try:
            self.logger.info("Registering with backend...")
            
            # Authenticate first
            if not await self.api_client.authenticate():
                self.logger.error("Authentication failed")
                return False
            
            # Register agent
            if await self.api_client.register_agent():
                self.registration_successful = True
                self.logger.info("Registration successful")
                return True
            else:
                self.logger.error("Registration failed")
                return False
                
        except Exception as e:
            self.logger.error(f"Registration error: {e}")
            return False
    
    async def _start_background_tasks(self):
        """Start background tasks."""
        # Heartbeat task
        heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        self._tasks.append(heartbeat_task)
        
        # Metrics collection task
        metrics_task = asyncio.create_task(self._metrics_loop())
        self._tasks.append(metrics_task)
        
        # Command processing task
        command_task = asyncio.create_task(self._command_loop())
        self._tasks.append(command_task)
        
        # Schedule monitoring (runs in separate thread)
        self._start_scheduler()
    
    def _start_scheduler(self):
        """Start the scheduler thread."""
        def run_scheduler():
            # Schedule periodic tasks
            schedule.every(self.config.update_check_interval).seconds.do(self._check_for_updates)
            
            while not self._schedule_stop_event.is_set():
                schedule.run_pending()
                time.sleep(1)
        
        self._scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        self._scheduler_thread.start()
    
    async def _heartbeat_loop(self):
        """Send periodic heartbeats to backend."""
        while self.running:
            try:
                if time.time() - self.last_heartbeat >= self.config.heartbeat_interval:
                    # Get basic metrics for heartbeat
                    basic_metrics = {
                        "agent_status": "running",
                        "libvirt_status": self.vm_operations.health_check()["status"],
                        "last_seen": datetime.now().isoformat()
                    }
                    
                    success = await self.api_client.send_heartbeat(basic_metrics)
                    if success:
                        self.last_heartbeat = time.time()
                        self.logger.debug("Heartbeat sent successfully")
                    else:
                        self.logger.warning("Heartbeat failed")
                
                await asyncio.sleep(5)  # Check every 5 seconds
                
            except Exception as e:
                self.logger.error(f"Heartbeat loop error: {e}")
                await asyncio.sleep(10)
    
    async def _metrics_loop(self):
        """Collect and send metrics periodically."""
        while self.running:
            try:
                if time.time() - self.last_metrics_collection >= self.config.metrics_interval:
                    self.logger.debug("Collecting metrics...")
                    
                    # Collect all metrics
                    metrics = self.metrics_collector.collect_all_metrics()
                    
                    # Send metrics to backend
                    success = await self.api_client.send_metrics(metrics)
                    if success:
                        self.last_metrics_collection = time.time()
                        self.logger.debug("Metrics sent successfully")
                    else:
                        self.logger.warning("Failed to send metrics")
                
                await asyncio.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                self.logger.error(f"Metrics loop error: {e}")
                await asyncio.sleep(30)
    
    async def _command_loop(self):
        """Check for and execute commands from backend."""
        while self.running:
            try:
                # Get pending commands
                commands = await self.api_client.get_commands()
                
                for command in commands:
                    await self._execute_command(command)
                
                await asyncio.sleep(5)  # Check every 5 seconds
                
            except Exception as e:
                self.logger.error(f"Command loop error: {e}")
                await asyncio.sleep(15)
    
    async def _execute_command(self, command: Dict[str, Any]):
        """Execute a single command."""
        command_id = command.get("id")
        command_type = command.get("type")
        
        self.logger.info(f"Executing command {command_id}: {command_type}")
        
        try:
            if command_type == "vm_operation":
                result = await self.vm_operations.execute_command(command.get("data", {}))
            elif command_type == "health_check":
                result = self.vm_operations.health_check()
            elif command_type == "collect_metrics":
                result = self.metrics_collector.collect_all_metrics()
            elif command_type == "agent_info":
                result = await self._get_agent_info()
            else:
                result = {
                    "success": False,
                    "message": f"Unknown command type: {command_type}"
                }
            
            # Add execution metadata
            result["command_id"] = command_id
            result["execution_time"] = datetime.now().isoformat()
            result["agent_id"] = self.agent_id
            
            # Report result back to backend
            await self.api_client.report_command_result(command_id, result)
            
            self.logger.info(f"Command {command_id} completed: {result.get('success', False)}")
            
        except Exception as e:
            self.logger.error(f"Command execution failed: {e}")
            
            error_result = {
                "success": False,
                "message": str(e),
                "error_type": type(e).__name__,
                "command_id": command_id,
                "execution_time": datetime.now().isoformat(),
                "agent_id": self.agent_id
            }
            
            await self.api_client.report_command_result(command_id, error_result)
    
    async def _get_agent_info(self) -> Dict[str, Any]:
        """Get comprehensive agent information."""
        return {
            "agent_id": self.agent_id,
            "agent_name": self.config.agent_name,
            "version": "1.0.0",
            "config": {
                "libvirt_uri": self.config.libvirt_uri,
                "metrics_interval": self.config.metrics_interval,
                "heartbeat_interval": self.config.heartbeat_interval,
                "auto_register": self.config.auto_register
            },
            "status": {
                "running": self.running,
                "registration_successful": self.registration_successful,
                "last_heartbeat": self.last_heartbeat,
                "last_metrics_collection": self.last_metrics_collection
            },
            "libvirt_health": self.vm_operations.health_check(),
            "timestamp": datetime.now().isoformat()
        }
    
    def _check_for_updates(self):
        """Check for agent updates (placeholder)."""
        self.logger.debug("Checking for updates...")
        # This is a placeholder for future update functionality
        pass
    
    async def run_forever(self):
        """Run the agent forever until stopped."""
        if not await self.start():
            return
        
        try:
            # Wait for all background tasks
            await asyncio.gather(*self._tasks, return_exceptions=True)
        except KeyboardInterrupt:
            self.logger.info("Received interrupt signal")
        finally:
            await self.stop()


def signal_handler(agent: VMAgent):
    """Handle shutdown signals."""
    def handler(signum, frame):
        agent.logger.info(f"Received signal {signum}")
        asyncio.create_task(agent.stop())
    
    return handler


async def main():
    """Main entry point."""
    # Load configuration
    config = load_config()
    
    # Setup logging
    setup_logging(config)
    
    # Create and start agent
    agent = VMAgent(config)
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler(agent))
    signal.signal(signal.SIGTERM, signal_handler(agent))
    
    # Run agent
    await agent.run_forever()


if __name__ == "__main__":
    asyncio.run(main())