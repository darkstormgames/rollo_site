"""XML template generation for libvirt domain definitions."""

import uuid
from typing import Dict, Any, List, Optional
from jinja2 import Template, Environment, DictLoader
import xml.etree.ElementTree as ET

from .exceptions import TemplateGenerationError
from core.config import settings


class XMLTemplateGenerator:
    """Generate XML templates for libvirt domain definitions."""
    
    def __init__(self):
        """Initialize template generator with predefined templates."""
        self.templates = {
            'basic_vm': '''
<domain type="kvm">
  <name>{{ name }}</name>
  <uuid>{{ uuid }}</uuid>
  <memory unit="MiB">{{ memory_mb }}</memory>
  <currentMemory unit="MiB">{{ memory_mb }}</currentMemory>
  <vcpu placement="static">{{ cpu_cores }}</vcpu>
  <os>
    <type arch="x86_64" machine="pc-q35-4.2">hvm</type>
    <boot dev="hd"/>
  </os>
  <features>
    <acpi/>
    <apic/>
    <vmport state="off"/>
  </features>
  <cpu mode="host-model" check="partial"/>
  <clock offset="utc">
    <timer name="rtc" tickpolicy="catchup"/>
    <timer name="pit" tickpolicy="delay"/>
    <timer name="hpet" present="no"/>
  </clock>
  <on_poweroff>destroy</on_poweroff>
  <on_reboot>restart</on_reboot>
  <on_crash>destroy</on_crash>
  <pm>
    <suspend-to-mem enabled="no"/>
    <suspend-to-disk enabled="no"/>
  </pm>
  <devices>
    <emulator>/usr/bin/qemu-system-x86_64</emulator>
    {% for disk in disks %}
    <disk type="file" device="disk">
      <driver name="qemu" type="qcow2"/>
      <source file="{{ disk.path }}"/>
      <target dev="{{ disk.target }}" bus="virtio"/>
    </disk>
    {% endfor %}
    {% for interface in network_interfaces %}
    <interface type="network">
      <source network="{{ interface.network }}"/>
      <model type="virtio"/>
      {% if interface.mac_address %}
      <mac address="{{ interface.mac_address }}"/>
      {% endif %}
    </interface>
    {% endfor %}
    <console type="pty">
      <target type="serial" port="0"/>
    </console>
    <channel type="unix">
      <target type="virtio" name="org.qemu.guest_agent.0"/>
    </channel>
    {% if vnc_enabled %}
    <graphics type="vnc" port="{{ vnc_port }}" autoport="yes" listen="0.0.0.0">
      <listen type="address" address="0.0.0.0"/>
    </graphics>
    {% endif %}
    <video>
      <model type="qxl" ram="65536" vram="65536" vgamem="16384" heads="1" primary="yes"/>
    </video>
  </devices>
</domain>''',
            
            'disk': '''
<disk type="file" device="disk">
  <driver name="qemu" type="{{ format }}" cache="{{ cache }}"/>
  <source file="{{ path }}"/>
  <target dev="{{ target }}" bus="{{ bus }}"/>
  {% if readonly %}
  <readonly/>
  {% endif %}
</disk>''',
            
            'network_interface': '''
<interface type="{{ type }}">
  {% if network %}
  <source network="{{ network }}"/>
  {% elif bridge %}
  <source bridge="{{ bridge }}"/>
  {% endif %}
  <model type="{{ model }}"/>
  {% if mac_address %}
  <mac address="{{ mac_address }}"/>
  {% endif %}
  {% if ip_address %}
  <ip address="{{ ip_address }}" prefix="{{ prefix }}"/>
  {% endif %}
</interface>''',

            'storage_pool': '''
<pool type="{{ type }}">
  <name>{{ name }}</name>
  <uuid>{{ uuid }}</uuid>
  <capacity unit="bytes">{{ capacity }}</capacity>
  <allocation unit="bytes">{{ allocation }}</allocation>
  <available unit="bytes">{{ available }}</available>
  <source>
    {% if type == 'dir' %}
    <dir path="{{ path }}"/>
    {% elif type == 'logical' %}
    <device path="{{ device }}"/>
    <name>{{ vg_name }}</name>
    <format type="{{ format }}"/>
    {% endif %}
  </source>
  <target>
    <path>{{ target_path }}</path>
    {% if permissions %}
    <permissions>
      <mode>{{ permissions.mode }}</mode>
      <owner>{{ permissions.owner }}</owner>
      <group>{{ permissions.group }}</group>
    </permissions>
    {% endif %}
  </target>
</pool>''',

            'storage_volume': '''
<volume type="{{ type }}">
  <name>{{ name }}</name>
  <key>{{ key }}</key>
  <source>
  </source>
  <capacity unit="bytes">{{ capacity }}</capacity>
  <allocation unit="bytes">{{ allocation }}</allocation>
  <target>
    <path>{{ path }}</path>
    <format type="{{ format }}"/>
    {% if permissions %}
    <permissions>
      <mode>{{ permissions.mode }}</mode>
      <owner>{{ permissions.owner }}</owner>
      <group>{{ permissions.group }}</group>
    </permissions>
    {% endif %}
  </target>
</volume>'''
        }
        
        self.env = Environment(loader=DictLoader(self.templates))
    
    def generate_vm_xml(self, **kwargs) -> str:
        """Generate VM domain XML.
        
        Args:
            **kwargs: VM configuration parameters.
            
        Returns:
            str: Generated XML string.
            
        Raises:
            TemplateGenerationError: If generation fails.
        """
        try:
            # Set defaults
            config = {
                'uuid': str(uuid.uuid4()),
                'memory_mb': 1024,
                'cpu_cores': 1,
                'disks': [],
                'network_interfaces': [{'network': 'default'}],
                'vnc_enabled': True,
                'vnc_port': -1,  # Auto-assign
                **kwargs
            }
            
            # Validate required fields
            if 'name' not in config:
                raise TemplateGenerationError('vm', 'VM name is required')
            
            template = self.env.get_template('basic_vm')
            xml_content = template.render(**config)
            
            # Validate XML
            self._validate_xml(xml_content)
            
            return xml_content
            
        except Exception as e:
            raise TemplateGenerationError('vm', str(e))
    
    def generate_disk_xml(self, path: str, target: str, bus: str = 'virtio', 
                         format: str = 'qcow2', cache: str = 'writeback',
                         readonly: bool = False) -> str:
        """Generate disk XML.
        
        Args:
            path: Disk file path.
            target: Target device (e.g., 'vda', 'vdb').
            bus: Disk bus type.
            format: Disk format.
            cache: Cache mode.
            readonly: Whether disk is readonly.
            
        Returns:
            str: Generated XML string.
        """
        try:
            template = self.env.get_template('disk')
            xml_content = template.render(
                path=path,
                target=target,
                bus=bus,
                format=format,
                cache=cache,
                readonly=readonly
            )
            
            self._validate_xml(xml_content)
            return xml_content
            
        except Exception as e:
            raise TemplateGenerationError('disk', str(e))
    
    def generate_network_interface_xml(self, interface_type: str = 'network',
                                     network: str = None, bridge: str = None,
                                     model: str = 'virtio', mac_address: str = None,
                                     ip_address: str = None, prefix: int = None) -> str:
        """Generate network interface XML.
        
        Args:
            interface_type: Interface type ('network', 'bridge').
            network: Network name (for network type).
            bridge: Bridge name (for bridge type).
            model: Network model.
            mac_address: MAC address.
            ip_address: Static IP address.
            prefix: IP prefix length.
            
        Returns:
            str: Generated XML string.
        """
        try:
            template = self.env.get_template('network_interface')
            xml_content = template.render(
                type=interface_type,
                network=network,
                bridge=bridge,
                model=model,
                mac_address=mac_address,
                ip_address=ip_address,
                prefix=prefix
            )
            
            self._validate_xml(xml_content)
            return xml_content
            
        except Exception as e:
            raise TemplateGenerationError('network_interface', str(e))
    
    def generate_storage_pool_xml(self, name: str, pool_type: str, **kwargs) -> str:
        """Generate storage pool XML.
        
        Args:
            name: Pool name.
            pool_type: Pool type ('dir', 'logical', etc.).
            **kwargs: Additional pool configuration.
            
        Returns:
            str: Generated XML string.
        """
        try:
            config = {
                'name': name,
                'type': pool_type,
                'uuid': str(uuid.uuid4()),
                **kwargs
            }
            
            template = self.env.get_template('storage_pool')
            xml_content = template.render(**config)
            
            self._validate_xml(xml_content)
            return xml_content
            
        except Exception as e:
            raise TemplateGenerationError('storage_pool', str(e))
    
    def generate_storage_volume_xml(self, name: str, capacity: int, **kwargs) -> str:
        """Generate storage volume XML.
        
        Args:
            name: Volume name.
            capacity: Volume capacity in bytes.
            **kwargs: Additional volume configuration.
            
        Returns:
            str: Generated XML string.
        """
        try:
            config = {
                'name': name,
                'type': 'file',
                'key': f"{settings.vm_storage_path}/{name}",
                'capacity': capacity,
                'allocation': kwargs.get('allocation', capacity),
                'path': f"{settings.vm_storage_path}/{name}",
                'format': 'qcow2',
                **kwargs
            }
            
            template = self.env.get_template('storage_volume')
            xml_content = template.render(**config)
            
            self._validate_xml(xml_content)
            return xml_content
            
        except Exception as e:
            raise TemplateGenerationError('storage_volume', str(e))
    
    def _validate_xml(self, xml_content: str):
        """Validate XML content.
        
        Args:
            xml_content: XML string to validate.
            
        Raises:
            TemplateGenerationError: If XML is invalid.
        """
        try:
            ET.fromstring(xml_content)
        except ET.ParseError as e:
            raise TemplateGenerationError('xml_validation', f"Invalid XML: {e}")
    
    def add_custom_template(self, name: str, template_content: str):
        """Add a custom template.
        
        Args:
            name: Template name.
            template_content: Jinja2 template content.
        """
        self.templates[name] = template_content
        self.env = Environment(loader=DictLoader(self.templates))
    
    def create_vm_from_template(self, vm_template: Dict[str, Any], 
                               overrides: Dict[str, Any] = None) -> str:
        """Create VM XML from a template configuration.
        
        Args:
            vm_template: Template configuration dictionary.
            overrides: Configuration overrides.
            
        Returns:
            str: Generated VM XML.
        """
        config = vm_template.copy()
        if overrides:
            config.update(overrides)
        
        return self.generate_vm_xml(**config)


# Global instance
xml_generator = XMLTemplateGenerator()