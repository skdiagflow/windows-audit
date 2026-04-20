"""Network Collector."""
import logging
from typing import Any, Dict, List

from ..utils import get_logger

logger = get_logger(__name__)


def get_network_collector() -> "NetworkCollector":
    """Get NetworkCollector instance."""
    return NetworkCollector()


def run_network_collector(engine) -> Dict[str, Any]:
    """Run network collector (convenience function)."""
    collector = NetworkCollector()
    return collector.collect(engine)


class NetworkCollector:
    """Collects network adapter and configuration information."""
    
    def __init__(self):
        self.name = "network"
        self.description = "Network adapters, IP config, WiFi profiles"
        self.requires_admin = False
    
    def collect(self, engine) -> Dict[str, Any]:
        """Collect network information.
        
        Args:
            engine: AuditEngine instance
            
        Returns:
            Network information dictionary
        """
        logger.info("Collecting network information...")
        
        data = {}
        
        # Get network adapters
        data["adapters"] = self._get_adapters(engine)
        
        # Get IP configuration
        data["ip_config"] = self._get_ip_config(engine)
        
        # Get WiFi profiles
        data["wifi_profiles"] = self._get_wifi_profiles(engine)
        
        # Get active connections
        data["connections"] = self._get_connections(engine)
        
        # Summary
        data["summary"] = self._get_summary(data["adapters"])
        
        logger.info(f"Network adapters: {len(data['adapters'])}")
        return data
    
    def _get_adapters(self, engine) -> List[Dict[str, Any]]:
        """Get network adapters."""
        adapters = []
        
        try:
            adapter_list = engine.wmi.get_class("Win32_NetworkAdapter")
            
            for adapter in adapter_list:
                # Filter to physical adapters
                if adapter.get("PhysicalAdapter") or adapter.get("AdapterType"):
                    adapters.append({
                        "name": adapter.get("Name"),
                        "adapter_type": adapter.get("AdapterType"),
                        "mac_address": adapter.get("MACAddress"),
                        "interface_index": adapter.get("Index"),
                        "service_name": adapter.get("ServiceName"),
                        "speed": adapter.get("Speed"),
                        "status": adapter.get("NetConnectionStatus"),
                        "physical_adapter": adapter.get("PhysicalAdapter"),
                        "device_id": adapter.get("DeviceID"),
                    })
                    
        except Exception as e:
            logger.warning(f"WMI network adapters query failed: {e}")
        
        return adapters
    
    def _get_ip_config(self, engine) -> List[Dict[str, Any]]:
        """Get IP configuration."""
        ip_config = []
        
        try:
            # Use PowerShell to get IP config
            cmd = """
            Get-NetIPConfiguration | Select-Object InterfaceAlias, IPv4Address, IPv4DefaultGateway, DNSServer | ConvertTo-Json -Depth 3
            """
            result = engine.ps.run(cmd, json_output=True)
            
            if isinstance(result, list):
                for config in result:
                    ip_config.append({
                        "interface": config.get("InterfaceAlias"),
                        "ipv4_address": self._extract_ipv4(config.get("IPv4Address")),
                        "gateway": self._extract_gateway(config.get("IPv4DefaultGateway")),
                        "dns_servers": self._extract_dns(config.get("DNSServer")),
                    })
            elif isinstance(result, dict):
                # Single adapter
                ip_config.append({
                    "interface": result.get("InterfaceAlias"),
                    "ipv4_address": self._extract_ipv4(result.get("IPv4Address")),
                    "gateway": self._extract_gateway(result.get("IPv4DefaultGateway")),
                    "dns_servers": self._extract_dns(result.get("DNSServer")),
                })
                
        except Exception as e:
            logger.debug(f"IP config query failed: {e}")
        
        return ip_config
    
    def _extract_ipv4(self, addr_info) -> List[str]:
        """Extract IPv4 addresses from config."""
        if not addr_info:
            return []
        
        if isinstance(addr_info, list):
            return [a.get("IPAddress") for a in addr_info if a.get("IPAddress")]
        elif isinstance(addr_info, dict):
            return [addr_info.get("IPAddress")]
        
        return []
    
    def _extract_gateway(self, gateway_info) -> List[str]:
        """Extract gateway from config."""
        if not gateway_info:
            return []
        
        if isinstance(gateway_info, list):
            return [g.get("NextHop") for g in gateway_info if g.get("NextHop")]
        elif isinstance(gateway_info, dict):
            return [gateway_info.get("NextHop")]
        
        return []
    
    def _extract_dns(self, dns_info) -> List[str]:
        """Extract DNS servers from config."""
        if not dns_info:
            return []
        
        if isinstance(dns_info, list):
            return [d.get("ServerAddresses") for d in dns_info if d.get("ServerAddresses")]
        elif isinstance(dns_info, dict):
            return dns_info.get("ServerAddresses", [])
        
        return []
    
    def _get_wifi_profiles(self, engine) -> List[Dict[str, Any]]:
        """Get WiFi profiles."""
        profiles = []
        
        try:
            cmd = "netsh wlan show profiles | Select-String 'All User Profile' | ForEach-Object { $_.Line.Split(':')[1].Trim() }"
            result = engine.ps.run(cmd)
            
            if result:
                profile_names = result.split("\n")
                for name in profile_names:
                    if name.strip():
                        # Get details for each profile
                        detail_cmd = f"netsh wlan show profile name='{name.strip()}' key=clear"
                        detail_result = engine.ps.run(detail_cmd)
                        
                        profile = {"name": name.strip()}
                        
                        # Parse authentication and cipher
                        if "WPA" in detail_result:
                            profile["security"] = "WPA"
                        elif "WEP" in detail_result:
                            profile["security"] = "WEP"
                        
                        profiles.append(profile)
                        
        except Exception as e:
            logger.debug(f"WiFi profiles query failed: {e}")
        
        return profiles
    
    def _get_connections(self, engine) -> List[Dict[str, Any]]:
        """Get active network connections."""
        connections = []
        
        try:
            cmd = "Get-NetTCPConnection | Where-Object {$_.State -eq 'Established'} | Select-Object LocalAddress, LocalPort, RemoteAddress, RemotePort, OwningProcess | ConvertTo-Json"
            result = engine.ps.run(cmd, json_output=True)
            
            if isinstance(result, list):
                # Limit to top 50
                for conn in result[:50]:
                    connections.append({
                        "local_address": conn.get("LocalAddress"),
                        "local_port": conn.get("LocalPort"),
                        "remote_address": conn.get("RemoteAddress"),
                        "remote_port": conn.get("RemotePort"),
                        "process_id": conn.get("OwningProcess"),
                    })
                    
        except Exception as e:
            logger.debug(f"Network connections query failed: {e}")
        
        return connections
    
    def _get_summary(self, adapters: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get network summary."""
        total = len(adapters)
        wifi = sum(1 for a in adapters if "Wi-Fi" in a.get("name", "") or "Wireless" in a.get("name", ""))
        ethernet = sum(1 for a in adapters if "Ethernet" in a.get("name", ""))
        
        return {
            "total": total,
            "wifi": wifi,
            "ethernet": ethernet,
        }