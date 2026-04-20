"""Local Users Collector."""
import logging
from typing import Any, Dict, List

from ..utils import get_logger

logger = get_logger(__name__)


def get_users_collector() -> "UsersCollector":
    """Get UsersCollector instance."""
    return UsersCollector()


def run_users_collector(engine) -> Dict[str, Any]:
    """Run users collector (convenience function)."""
    collector = UsersCollector()
    return collector.collect(engine)


class UsersCollector:
    """Collects local user account information."""
    
    def __init__(self):
        self.name = "users"
        self.description = "Local user accounts"
        self.requires_admin = True
    
    def collect(self, engine) -> Dict[str, Any]:
        """Collect local user information.
        
        Args:
            engine: AuditEngine instance
            
        Returns:
            User information dictionary
        """
        logger.info("Collecting local users...")
        
        data = {}
        
        # Get local users from WMI
        data["local_users"] = self._get_local_users(engine)
        
        # Get current user info
        data["current_user"] = self._get_current_user(engine)
        
        # Count summary
        data["summary"] = self._get_summary(data["local_users"])
        
        logger.info(f"Users collected: {data['summary']['total']} total")
        return data
    
    def _get_local_users(self, engine) -> List[Dict[str, Any]]:
        """Get local user accounts."""
        users = []
        
        try:
            # Query WMI for user accounts
            user_list = engine.wmi.query(
                "SELECT * FROM Win32_UserAccount WHERE LocalAccount = True"
            )
            
            for user in user_list:
                users.append({
                    "name": user.get("Name"),
                    "full_name": user.get("FullName"),
                    "disabled": user.get("Disabled", False),
                    "lockout": user.get("Lockout", False),
                    "password_required": user.get("PasswordRequired", True),
                    "password_expires": user.get("PasswordExpires", True),
                    "password_changeable": user.get("PasswordChangeable", True),
                    "account_type": user.get("AccountType"),
                    "domain": user.get("Domain"),
                    "sid": user.get("SID"),
                    "status": user.get("Status"),
                    "description": user.get("Description"),
                })
                
        except Exception as e:
            logger.warning(f"WMI users query failed: {e}")
        
        return users
    
    def _get_current_user(self, engine) -> Dict[str, Any]:
        """Get current user information."""
        try:
            # Use PowerShell to get current user
            cmd = """
            @{
                UserName = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
                IsAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
            } | ConvertTo-Json
            """
            result = engine.ps.run(cmd, json_output=True)
            if isinstance(result, dict):
                return result
        except Exception as e:
            logger.debug(f"Current user query failed: {e}")
        
        return {"UserName": "Unknown", "IsAdmin": False}
    
    def _get_summary(self, users: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get user account summary."""
        total = len(users)
        disabled = sum(1 for u in users if u.get("disabled"))
        locked = sum(1 for u in users if u.get("lockout"))
        
        return {
            "total": total,
            "enabled": total - disabled,
            "disabled": disabled,
            "locked": locked,
        }