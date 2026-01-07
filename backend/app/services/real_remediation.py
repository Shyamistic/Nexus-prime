import asyncio
import logging
from typing import Dict, Any, List
from datetime import datetime

from app.core.config import settings

logger = logging.getLogger(__name__)

class RemediationService:
    def __init__(self):
        self.enabled = getattr(settings, 'REMEDIATION_ENABLED', True)
        self.dry_run = getattr(settings, 'REMEDIATION_DRY_RUN', False)
        
    async def execute_remediation_steps(self, incident_id: str, remediation_steps: List[str]) -> Dict[str, Any]:
        """Execute REAL remediation steps based on AI analysis"""
        logger.info(f"🔧 Starting REAL remediation for incident {incident_id}")
        
        if not self.enabled:
            logger.info(f"🔧 Remediation disabled, skipping execution")
            return {"status": "skipped", "reason": "remediation_disabled"}
        
        results = []
        
        for i, step in enumerate(remediation_steps):
            logger.info(f"🔧 EXECUTING REAL STEP {i+1}/{len(remediation_steps)}: {step}")
            
            try:
                result = await self._execute_step(step)
                results.append({
                    "step": step,
                    "status": "success" if result["success"] else "failed",
                    "output": result["output"],
                    "executed_at": datetime.utcnow().isoformat()
                })
                
                if result["success"]:
                    logger.info(f"✅ REAL STEP COMPLETED: {step}")
                else:
                    logger.error(f"❌ REAL STEP FAILED: {result['output']}")
                    
            except Exception as e:
                logger.error(f"❌ Step execution error: {e}")
                results.append({
                    "step": step,
                    "status": "error",
                    "output": str(e),
                    "executed_at": datetime.utcnow().isoformat()
                })
        
        success_count = len([r for r in results if r["status"] == "success"])
        
        return {
            "status": "completed",
            "total_steps": len(remediation_steps),
            "successful_steps": success_count,
            "results": results
        }
    
    async def _execute_step(self, step: str) -> Dict[str, Any]:
        """Execute a single REAL remediation step"""
        
        step_lower = step.lower()
        
        if "restart" in step_lower and "service" in step_lower:
            return await self._restart_service(step)
        elif "scale" in step_lower:
            return await self._scale_service(step)
        elif "clear" in step_lower and "cache" in step_lower:
            return await self._clear_cache(step)
        elif "increase" in step_lower and ("memory" in step_lower or "cpu" in step_lower):
            return await self._increase_resources(step)
        elif "rollback" in step_lower:
            return await self._rollback_deployment(step)
        elif "enable" in step_lower or "disable" in step_lower:
            return await self._toggle_feature(step)
        else:
            return await self._execute_custom_command(step)
    
    async def _restart_service(self, step: str) -> Dict[str, Any]:
        """RESTART REAL SERVICES - Kubernetes, Docker, systemctl"""
        service_name = self._extract_service_name(step)
        
        if self.dry_run:
            return {"success": True, "output": f"DRY RUN: Would restart {service_name}"}
        
        logger.info(f"🔧 EXECUTING REAL SERVICE RESTART: {service_name}")
        
        # Try multiple restart methods
        commands = [
            f"kubectl rollout restart deployment/{service_name}",
            f"docker restart {service_name}",
            f"sudo systemctl restart {service_name}",
            f"pm2 restart {service_name}"
        ]
        
        for cmd in commands:
            result = await self._run_command(cmd)
            if result["success"]:
                logger.info(f"✅ SERVICE RESTARTED: {service_name} via {cmd}")
                return result
        
        return {"success": False, "output": f"Failed to restart {service_name} with any method"}
    
    async def _clear_cache(self, step: str) -> Dict[str, Any]:
        """CLEAR REAL CACHE - Redis, Memcached, Application Cache"""
        if self.dry_run:
            return {"success": True, "output": "DRY RUN: Would clear cache"}
        
        logger.info(f"🔧 EXECUTING REAL CACHE CLEAR")
        
        commands = [
            "redis-cli FLUSHALL",
            "echo 'flush_all' | nc localhost 11211",
            "curl -X POST http://localhost:8080/admin/cache/clear"
        ]
        
        for cmd in commands:
            result = await self._run_command(cmd)
            if result["success"]:
                logger.info(f"✅ CACHE CLEARED via {cmd}")
                return result
        
        return {"success": False, "output": "Failed to clear cache with any method"}
    
    async def _scale_service(self, step: str) -> Dict[str, Any]:
        """SCALE REAL SERVICES"""
        service_name = self._extract_service_name(step)
        replicas = self._extract_number(step, default=3)
        
        if self.dry_run:
            return {"success": True, "output": f"DRY RUN: Would scale {service_name} to {replicas}"}
        
        logger.info(f"🔧 EXECUTING REAL SERVICE SCALING: {service_name} to {replicas} replicas")
        
        result = await self._run_command(f"kubectl scale deployment/{service_name} --replicas={replicas}")
        if result["success"]:
            logger.info(f"✅ SERVICE SCALED: {service_name} to {replicas} replicas")
        
        return result
    
    async def _increase_resources(self, step: str) -> Dict[str, Any]:
        """INCREASE REAL RESOURCES"""
        service_name = self._extract_service_name(step)
        
        if self.dry_run:
            return {"success": True, "output": f"DRY RUN: Would increase resources for {service_name}"}
        
        logger.info(f"🔧 EXECUTING REAL RESOURCE INCREASE: {service_name}")
        
        if "memory" in step.lower():
            cmd = f"kubectl patch deployment {service_name} -p '{{\"spec\":{{\"template\":{{\"spec\":{{\"containers\":[{{\"name\":\"{service_name}\",\"resources\":{{\"requests\":{{\"memory\":\"1Gi\"}},\"limits\":{{\"memory\":\"2Gi\"}}}}}}]}}}}}}'"
        else:
            cmd = f"kubectl patch deployment {service_name} -p '{{\"spec\":{{\"template\":{{\"spec\":{{\"containers\":[{{\"name\":\"{service_name}\",\"resources\":{{\"requests\":{{\"cpu\":\"500m\"}},\"limits\":{{\"cpu\":\"1000m\"}}}}}}]}}}}}}'"
        
        result = await self._run_command(cmd)
        if result["success"]:
            logger.info(f"✅ RESOURCES INCREASED: {service_name}")
        
        return result
    
    async def _rollback_deployment(self, step: str) -> Dict[str, Any]:
        """ROLLBACK REAL DEPLOYMENT"""
        service_name = self._extract_service_name(step)
        
        if self.dry_run:
            return {"success": True, "output": f"DRY RUN: Would rollback {service_name}"}
        
        logger.info(f"🔧 EXECUTING REAL DEPLOYMENT ROLLBACK: {service_name}")
        
        result = await self._run_command(f"kubectl rollout undo deployment/{service_name}")
        if result["success"]:
            logger.info(f"✅ DEPLOYMENT ROLLED BACK: {service_name}")
        
        return result
    
    async def _toggle_feature(self, step: str) -> Dict[str, Any]:
        """TOGGLE REAL FEATURE FLAGS"""
        action = "enable" if "enable" in step.lower() else "disable"
        feature_name = self._extract_feature_name(step)
        
        if self.dry_run:
            return {"success": True, "output": f"DRY RUN: Would {action} feature {feature_name}"}
        
        logger.info(f"🔧 EXECUTING REAL FEATURE TOGGLE: {action} {feature_name}")
        
        # Real feature flag toggle (customize for your system)
        result = await self._run_command(f"curl -X POST http://localhost:8080/admin/features/{feature_name}/{action}")
        if result["success"]:
            logger.info(f"✅ FEATURE TOGGLED: {feature_name} {action}d")
        
        return result
    
    async def _execute_custom_command(self, step: str) -> Dict[str, Any]:
        """EXECUTE REAL CUSTOM COMMANDS"""
        if self.dry_run:
            return {"success": True, "output": f"DRY RUN: Would execute {step}"}
        
        # Enhanced safe command list for production
        safe_commands = [
            'kubectl', 'docker', 'curl', 'systemctl', 'service', 'nginx', 'apache2',
            'redis-cli', 'mysql', 'psql', 'mongo', 'pm2', 'supervisorctl',
            'aws', 'az', 'gcloud', 'terraform', 'helm', 'istioctl'
        ]
        
        if not any(cmd in step.lower() for cmd in safe_commands):
            return {"success": False, "output": "Command not in safe list for security"}
        
        logger.info(f"🔧 EXECUTING REAL CUSTOM COMMAND: {step}")
        
        result = await self._run_command(step)
        if result["success"]:
            logger.info(f"✅ CUSTOM COMMAND EXECUTED: {step}")
        else:
            logger.error(f"❌ CUSTOM COMMAND FAILED: {step}")
        
        return result
    
    async def _run_command(self, command: str) -> Dict[str, Any]:
        """RUN REAL SYSTEM COMMANDS with safety and logging"""
        try:
            logger.info(f"🔧 EXECUTING SYSTEM COMMAND: {command}")
            
            process = await asyncio.wait_for(
                asyncio.create_subprocess_shell(
                    command,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                ),
                timeout=30.0
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=60.0
            )
            
            stdout_text = stdout.decode().strip()
            stderr_text = stderr.decode().strip()
            
            if process.returncode == 0:
                logger.info(f"✅ COMMAND SUCCESS: {stdout_text[:100]}...")
                return {"success": True, "output": stdout_text}
            else:
                logger.error(f"❌ COMMAND FAILED (code {process.returncode}): {stderr_text[:100]}...")
                return {"success": False, "output": stderr_text or stdout_text}
                
        except asyncio.TimeoutError:
            logger.error(f"❌ COMMAND TIMEOUT: {command}")
            return {"success": False, "output": "Command execution timed out"}
        except Exception as e:
            logger.error(f"❌ COMMAND ERROR: {e}")
            return {"success": False, "output": str(e)}
    
    def _extract_service_name(self, step: str) -> str:
        """Extract service name from remediation step"""
        words = step.lower().split()
        
        for i, word in enumerate(words):
            if word in ['service', 'deployment', 'pod', 'container'] and i + 1 < len(words):
                return words[i + 1]
        
        # Common service patterns
        services = ['api', 'web', 'database', 'cache', 'auth', 'payment', 'gateway', 'frontend', 'backend']
        for service in services:
            if service in step.lower():
                return service
        
        return "app-service"
    
    def _extract_number(self, step: str, default: int = 1) -> int:
        """Extract number from step"""
        import re
        numbers = re.findall(r'\d+', step)
        return int(numbers[0]) if numbers else default
    
    def _extract_feature_name(self, step: str) -> str:
        """Extract feature name from step"""
        words = step.lower().split()
        for i, word in enumerate(words):
            if word in ['feature', 'flag'] and i + 1 < len(words):
                return words[i + 1]
        return "feature-flag"

# Global instance
remediation_service = RemediationService()