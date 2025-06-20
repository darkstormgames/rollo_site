"""Background metrics collection service."""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List
from sqlalchemy.orm import Session

from models.base import DatabaseSession
from models.server import Server, ServerStatus
from models.virtual_machine import VirtualMachine, VMStatus
from services.metrics_service import MetricsService
from services.alerts_service import AlertsService
from agent.metrics import MetricsCollector
from virtualization.monitoring import VMMonitoring
from core.logging import get_logger

logger = get_logger("metrics_collection")


class MetricsCollectionService:
    """Background service for automatic metrics collection."""
    
    def __init__(self):
        self.is_running = False
        self.collection_interval = 5  # seconds
        self.metrics_collector = MetricsCollector()
        self.vm_monitoring = VMMonitoring()
        
    async def start_collection(self):
        """Start the metrics collection service."""
        if self.is_running:
            logger.warning("Metrics collection service is already running")
            return
        
        self.is_running = True
        logger.info("Starting metrics collection service...")
        
        try:
            while self.is_running:
                await self._collect_all_metrics()
                await asyncio.sleep(self.collection_interval)
        except Exception as e:
            logger.error(f"Metrics collection service error: {e}")
        finally:
            self.is_running = False
            logger.info("Metrics collection service stopped")
    
    def stop_collection(self):
        """Stop the metrics collection service."""
        self.is_running = False
        logger.info("Stopping metrics collection service...")
    
    async def _collect_all_metrics(self):
        """Collect metrics for all servers and VMs."""
        try:
            with DatabaseSession.get_session() as db:
                metrics_service = MetricsService(db)
                
                # Collect server metrics
                await self._collect_server_metrics(db, metrics_service)
                
                # Collect VM metrics
                await self._collect_vm_metrics(db, metrics_service)
                
                # Check alerts
                await self._check_alerts(db)
                
        except Exception as e:
            logger.error(f"Error during metrics collection: {e}")
    
    async def _collect_server_metrics(self, db: Session, metrics_service: MetricsService):
        """Collect metrics for all servers."""
        try:
            servers = db.query(Server).filter(Server.status == ServerStatus.ONLINE).all()
            
            for server in servers:
                try:
                    # Get system metrics from agent (in a real system, this would be remote)
                    system_metrics = self.metrics_collector.collect_system_metrics()
                    
                    if system_metrics:
                        # Record CPU metrics
                        if 'cpu' in system_metrics:
                            cpu_data = system_metrics['cpu']
                            if 'usage_percent' in cpu_data:
                                metrics_service.record_server_metric(
                                    server.id, 'cpu_usage', cpu_data['usage_percent'], 'percent'
                                )
                        
                        # Record memory metrics
                        if 'memory' in system_metrics:
                            memory_data = system_metrics['memory']
                            if 'percent' in memory_data:
                                metrics_service.record_server_metric(
                                    server.id, 'memory_usage', memory_data['percent'], 'percent'
                                )
                        
                        # Record disk metrics
                        if 'disk' in system_metrics:
                            disk_data = system_metrics['disk']
                            if 'percent' in disk_data:
                                metrics_service.record_server_metric(
                                    server.id, 'disk_usage', disk_data['percent'], 'percent'
                                )
                        
                        # Record network metrics
                        if 'network' in system_metrics:
                            network_data = system_metrics['network']
                            if 'bytes_recv' in network_data:
                                metrics_service.record_server_metric(
                                    server.id, 'network_rx_bytes', network_data['bytes_recv'], 'bytes'
                                )
                            if 'bytes_sent' in network_data:
                                metrics_service.record_server_metric(
                                    server.id, 'network_tx_bytes', network_data['bytes_sent'], 'bytes'
                                )
                        
                        # Record system metrics
                        if 'system' in system_metrics:
                            system_data = system_metrics['system']
                            if 'load_average' in system_data and system_data['load_average']:
                                avg_load = sum(system_data['load_average']) / len(system_data['load_average'])
                                metrics_service.record_server_metric(
                                    server.id, 'load_average', avg_load, 'count'
                                )
                        
                        logger.debug(f"Collected metrics for server {server.hostname}")
                        
                except Exception as e:
                    logger.error(f"Error collecting metrics for server {server.hostname}: {e}")
                    
        except Exception as e:
            logger.error(f"Error in server metrics collection: {e}")
    
    async def _collect_vm_metrics(self, db: Session, metrics_service: MetricsService):
        """Collect metrics for all VMs."""
        try:
            vms = db.query(VirtualMachine).filter(VirtualMachine.status == VMStatus.RUNNING).all()
            
            for vm in vms:
                try:
                    # Get VM metrics from libvirt
                    vm_metrics = await self.vm_monitoring.get_vm_metrics(uuid=vm.uuid)
                    
                    if vm_metrics:
                        # Record CPU metrics
                        if 'cpu_stats' in vm_metrics:
                            cpu_stats = vm_metrics['cpu_stats']
                            if 'usage_percent' in cpu_stats:
                                metrics_service.record_vm_metric(
                                    vm.id, 'cpu_usage', cpu_stats['usage_percent'], 'percent'
                                )
                            if 'steal_time' in cpu_stats:
                                metrics_service.record_vm_metric(
                                    vm.id, 'cpu_steal_time', cpu_stats['steal_time'], 'percent'
                                )
                        
                        # Record memory metrics
                        if 'memory_stats' in vm_metrics:
                            memory_stats = vm_metrics['memory_stats']
                            if 'usage_percent' in memory_stats:
                                metrics_service.record_vm_metric(
                                    vm.id, 'memory_usage', memory_stats['usage_percent'], 'percent'
                                )
                            if 'active' in memory_stats:
                                metrics_service.record_vm_metric(
                                    vm.id, 'memory_active', memory_stats['active'] / 1024, 'mb'
                                )
                        
                        # Record disk metrics
                        if 'disk_stats' in vm_metrics:
                            total_read_ops = 0
                            total_write_ops = 0
                            total_read_bytes = 0
                            total_write_bytes = 0
                            
                            for device_stats in vm_metrics['disk_stats'].values():
                                total_read_ops += device_stats.get('read_requests', 0)
                                total_write_ops += device_stats.get('write_requests', 0)
                                total_read_bytes += device_stats.get('read_bytes', 0)
                                total_write_bytes += device_stats.get('write_bytes', 0)
                            
                            metrics_service.record_vm_metric(vm.id, 'disk_read_ops', total_read_ops, 'count')
                            metrics_service.record_vm_metric(vm.id, 'disk_write_ops', total_write_ops, 'count')
                            metrics_service.record_vm_metric(vm.id, 'disk_read_bytes', total_read_bytes, 'bytes')
                            metrics_service.record_vm_metric(vm.id, 'disk_write_bytes', total_write_bytes, 'bytes')
                        
                        # Record network metrics
                        if 'network_stats' in vm_metrics:
                            total_rx_bytes = 0
                            total_tx_bytes = 0
                            total_rx_packets = 0
                            total_tx_packets = 0
                            
                            for interface_stats in vm_metrics['network_stats'].values():
                                total_rx_bytes += interface_stats.get('rx_bytes', 0)
                                total_tx_bytes += interface_stats.get('tx_bytes', 0)
                                total_rx_packets += interface_stats.get('rx_packets', 0)
                                total_tx_packets += interface_stats.get('tx_packets', 0)
                            
                            metrics_service.record_vm_metric(vm.id, 'network_rx_bytes', total_rx_bytes, 'bytes')
                            metrics_service.record_vm_metric(vm.id, 'network_tx_bytes', total_tx_bytes, 'bytes')
                            metrics_service.record_vm_metric(vm.id, 'network_rx_packets', total_rx_packets, 'count')
                            metrics_service.record_vm_metric(vm.id, 'network_tx_packets', total_tx_packets, 'count')
                        
                        # Calculate and record performance metrics
                        if 'performance_metrics' in vm_metrics:
                            perf_metrics = vm_metrics['performance_metrics']
                            if 'total_disk_read_bytes' in perf_metrics and 'total_disk_write_bytes' in perf_metrics:
                                total_io = perf_metrics['total_disk_read_bytes'] + perf_metrics['total_disk_write_bytes']
                                if total_io > 0:
                                    # Simplified IOPS calculation
                                    iops = (total_read_ops + total_write_ops) / self.collection_interval if (total_read_ops + total_write_ops) > 0 else 0
                                    metrics_service.record_vm_metric(vm.id, 'iops', iops, 'ops/sec')
                        
                        logger.debug(f"Collected metrics for VM {vm.name}")
                        
                except Exception as e:
                    logger.error(f"Error collecting metrics for VM {vm.name}: {e}")
                    
        except Exception as e:
            logger.error(f"Error in VM metrics collection: {e}")
    
    async def _check_alerts(self, db: Session):
        """Check for triggered alerts."""
        try:
            alerts_service = AlertsService(db)
            triggered_alerts = alerts_service.check_threshold_alerts()
            
            if triggered_alerts:
                logger.info(f"Found {len(triggered_alerts)} triggered alerts")
                
                # In a real system, you would send notifications here
                for alert in triggered_alerts:
                    logger.warning(
                        f"ALERT: {alert.rule_name} - {alert.entity_type.value} {alert.entity_name} "
                        f"{alert.metric_type.value} is {alert.current_value} (threshold: {alert.threshold})"
                    )
                    
        except Exception as e:
            logger.error(f"Error checking alerts: {e}")


# Global instance
metrics_collection_service = MetricsCollectionService()