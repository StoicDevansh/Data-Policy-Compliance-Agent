"""
Monitoring Scheduler - Periodic compliance monitoring with APScheduler.
"""
import asyncio
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime
from loguru import logger

try:
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    from apscheduler.triggers.interval import IntervalTrigger
    from apscheduler.triggers.cron import CronTrigger
    SCHEDULER_AVAILABLE = True
except ImportError:
    SCHEDULER_AVAILABLE = False


class MonitoringScheduler:
    """
    Schedules and manages periodic compliance monitoring jobs.
    """
    
    def __init__(
        self,
        agent: Any,
        interval_seconds: int = 3600,
        callback: Optional[Callable] = None
    ):
        """
        Initialize monitoring scheduler.
        
        Args:
            agent: DataPolicyAgent instance
            interval_seconds: Default monitoring interval
            callback: Optional callback for new violations
        """
        self.agent = agent
        self.interval_seconds = interval_seconds
        self.callback = callback
        self.scheduler = None
        self.is_running = False
        self.job_history: List[Dict[str, Any]] = []
        self.last_run: Optional[str] = None
        self.violation_trends: List[Dict[str, Any]] = []
        
        if not SCHEDULER_AVAILABLE:
            logger.warning("APScheduler not available. Install with: pip install apscheduler")
    
    async def start(self):
        """Start the monitoring scheduler."""
        if not SCHEDULER_AVAILABLE:
            logger.error("Cannot start scheduler: APScheduler not available")
            return
        
        if self.is_running:
            logger.warning("Scheduler is already running")
            return
        
        self.scheduler = AsyncIOScheduler()
        
        # Add main monitoring job
        self.scheduler.add_job(
            self._run_monitoring_job,
            IntervalTrigger(seconds=self.interval_seconds),
            id='compliance_monitoring',
            name='Periodic Compliance Monitoring',
            replace_existing=True
        )
        
        self.scheduler.start()
        self.is_running = True
        
        logger.info(f"Started monitoring scheduler (interval: {self.interval_seconds}s)")
        
        # Run initial scan
        await self._run_monitoring_job()
    
    async def stop(self):
        """Stop the monitoring scheduler."""
        if self.scheduler and self.is_running:
            self.scheduler.shutdown(wait=False)
            self.is_running = False
            logger.info("Stopped monitoring scheduler")
    
    async def _run_monitoring_job(self):
        """Execute a monitoring job."""
        job_id = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        logger.info(f"Running monitoring job: {job_id}")
        
        job_record = {
            "job_id": job_id,
            "started_at": datetime.utcnow().isoformat(),
            "status": "running"
        }
        
        try:
            # Run compliance scan
            violations = await self.agent.scan_for_violations()
            
            job_record["completed_at"] = datetime.utcnow().isoformat()
            job_record["status"] = "completed"
            job_record["violations_found"] = len(violations)
            
            # Track new violations (compared to last run)
            new_violations = self._identify_new_violations(violations)
            job_record["new_violations"] = len(new_violations)
            
            # Update trends
            self._update_trends(violations)
            
            # Invoke callback if new violations found
            if new_violations and self.callback:
                try:
                    if asyncio.iscoroutinefunction(self.callback):
                        await self.callback(new_violations)
                    else:
                        self.callback(new_violations)
                except Exception as e:
                    logger.error(f"Callback error: {e}")
            
            self.last_run = datetime.utcnow().isoformat()
            
            logger.info(f"Monitoring job {job_id} completed: {len(violations)} total, {len(new_violations)} new violations")
            
        except Exception as e:
            job_record["status"] = "failed"
            job_record["error"] = str(e)
            logger.error(f"Monitoring job {job_id} failed: {e}")
        
        self.job_history.append(job_record)
        
        # Keep only last 100 job records
        if len(self.job_history) > 100:
            self.job_history = self.job_history[-100:]
    
    def _identify_new_violations(
        self,
        current_violations: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Identify violations that are new since last run."""
        # Get existing violation signatures
        existing_signatures = set()
        for v in self.agent.violations[:-len(current_violations)] if len(self.agent.violations) > len(current_violations) else []:
            sig = f"{v.get('table')}:{v.get('column')}:{v.get('rule_id')}"
            existing_signatures.add(sig)
        
        # Find new violations
        new_violations = []
        for v in current_violations:
            sig = f"{v.get('table')}:{v.get('column')}:{v.get('rule_id')}"
            if sig not in existing_signatures:
                new_violations.append(v)
        
        return new_violations
    
    def _update_trends(self, violations: List[Dict[str, Any]]):
        """Update violation trends for reporting."""
        trend_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "total_violations": len(violations),
            "by_severity": {},
            "by_type": {}
        }
        
        for v in violations:
            sev = v.get('severity', 'unknown')
            typ = v.get('rule_type', 'unknown')
            
            trend_entry["by_severity"][sev] = trend_entry["by_severity"].get(sev, 0) + 1
            trend_entry["by_type"][typ] = trend_entry["by_type"].get(typ, 0) + 1
        
        self.violation_trends.append(trend_entry)
        
        # Keep only last 30 days of trends (assuming hourly checks = 720 entries)
        if len(self.violation_trends) > 720:
            self.violation_trends = self.violation_trends[-720:]
    
    async def add_custom_job(
        self,
        job_id: str,
        func: Callable,
        trigger_type: str = "interval",
        **trigger_kwargs
    ):
        """
        Add a custom monitoring job.
        
        Args:
            job_id: Unique job identifier
            func: Function to execute
            trigger_type: 'interval' or 'cron'
            **trigger_kwargs: Trigger-specific arguments
        """
        if not self.scheduler:
            logger.error("Scheduler not initialized. Call start() first.")
            return
        
        if trigger_type == "interval":
            trigger = IntervalTrigger(**trigger_kwargs)
        elif trigger_type == "cron":
            trigger = CronTrigger(**trigger_kwargs)
        else:
            raise ValueError(f"Unknown trigger type: {trigger_type}")
        
        self.scheduler.add_job(
            func,
            trigger,
            id=job_id,
            replace_existing=True
        )
        
        logger.info(f"Added custom job: {job_id}")
    
    async def remove_job(self, job_id: str):
        """Remove a scheduled job."""
        if self.scheduler:
            self.scheduler.remove_job(job_id)
            logger.info(f"Removed job: {job_id}")
    
    def get_job_status(self) -> Dict[str, Any]:
        """Get current scheduler status and job information."""
        jobs = []
        if self.scheduler:
            for job in self.scheduler.get_jobs():
                jobs.append({
                    "id": job.id,
                    "name": job.name,
                    "next_run": str(job.next_run_time) if job.next_run_time else None
                })
        
        return {
            "is_running": self.is_running,
            "interval_seconds": self.interval_seconds,
            "last_run": self.last_run,
            "jobs": jobs,
            "job_history_count": len(self.job_history),
            "trend_data_points": len(self.violation_trends)
        }
    
    def get_trends(self, limit: int = 24) -> List[Dict[str, Any]]:
        """Get recent violation trends."""
        return self.violation_trends[-limit:]
    
    def get_trend_summary(self) -> Dict[str, Any]:
        """Get trend summary with change indicators."""
        if len(self.violation_trends) < 2:
            return {"insufficient_data": True}
        
        latest = self.violation_trends[-1]
        previous = self.violation_trends[-2]
        
        # Calculate changes
        total_change = latest["total_violations"] - previous["total_violations"]
        
        severity_changes = {}
        for sev in ['critical', 'high', 'medium', 'low']:
            latest_count = latest["by_severity"].get(sev, 0)
            prev_count = previous["by_severity"].get(sev, 0)
            severity_changes[sev] = {
                "current": latest_count,
                "previous": prev_count,
                "change": latest_count - prev_count
            }
        
        return {
            "timestamp": latest["timestamp"],
            "total_violations": latest["total_violations"],
            "total_change": total_change,
            "trend_direction": "increasing" if total_change > 0 else ("decreasing" if total_change < 0 else "stable"),
            "severity_changes": severity_changes
        }
