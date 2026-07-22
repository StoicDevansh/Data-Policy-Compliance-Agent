"""
Monitoring Scheduler - Handles periodic compliance scanning
"""
import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Optional, Callable, Dict, Any, Awaitable


class MonitoringScheduler:
    """
    Scheduler for periodic compliance scanning operations.
    Runs automated scans at configured intervals and handles callbacks for results.
    """

    def __init__(
        self,
        agent: Any,
        interval_seconds: int = 3600,
        callback: Optional[Callable[[Dict[str, Any]], Awaitable[None]]] = None
    ):
        """
        Initialize the monitoring scheduler.

        Args:
            agent: The DataPolicyAgent instance to run scans on
            interval_seconds: Interval between scans in seconds (default: 1 hour)
            callback: Optional async callback function to handle scan results
        """
        self.agent = agent
        self.interval_seconds = interval_seconds
        self.callback = callback
        self.scheduler_task: Optional[asyncio.Task] = None
        self.is_running = False
        self.scheduler_id = str(uuid.uuid4())
        self.next_scheduled_run: Optional[datetime] = None
        self.last_run_time: Optional[datetime] = None
        self.error_count = 0
        self.success_count = 0

    async def start(self) -> bool:
        """
        Start the monitoring scheduler.

        Returns:
            True if scheduler started successfully, False otherwise
        """
        if self.is_running:
            return False

        self.is_running = True
        self.scheduler_task = asyncio.create_task(self._monitoring_loop())
        return True

    async def stop(self) -> bool:
        """
        Stop the monitoring scheduler.

        Returns:
            True if scheduler stopped successfully, False otherwise
        """
        if not self.is_running:
            return False

        self.is_running = False
        if self.scheduler_task:
            self.scheduler_task.cancel()
            try:
                await self.scheduler_task
            except asyncio.CancelledError:
                pass
            self.scheduler_task = None

        return True

    async def _monitoring_loop(self) -> None:
        """Main monitoring loop that runs periodic scans."""
        while self.is_running:
            try:
                # Calculate next run time
                self.next_scheduled_run = datetime.utcnow() + timedelta(seconds=self.interval_seconds)

                # Wait for the interval
                await asyncio.sleep(self.interval_seconds)

                # Run the scan if still active
                if self.is_running:
                    await self._run_scheduled_scan()

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.error_count += 1
                # Continue the loop despite errors
                await asyncio.sleep(min(60, self.interval_seconds))  # Wait before retrying

    async def _run_scheduled_scan(self) -> None:
        """Run a scheduled compliance scan."""
        try:
            self.last_run_time = datetime.utcnow()

            # Run a basic compliance scan
            scan_results = await self.agent.scan_for_violations()

            # Update success count
            self.success_count += 1

            # Call the callback if provided
            if self.callback:
                await self.callback(scan_results)

        except Exception as e:
            self.error_count += 1
            # In a real implementation, we would log this error
            pass

    async def run_immediate_scan(self) -> Dict[str, Any]:
        """
        Run an immediate compliance scan outside of the schedule.

        Returns:
            Results from the compliance scan
        """
        try:
            scan_results = await self.agent.scan_for_violations()
            self.last_run_time = datetime.utcnow()
            self.success_count += 1
            return scan_results
        except Exception as e:
            self.error_count += 1
            raise e

    def get_schedule_status(self) -> Dict[str, Any]:
        """
        Get the current status of the scheduler.

        Returns:
            Dictionary with scheduler status information
        """
        return {
            'scheduler_id': self.scheduler_id,
            'is_running': self.is_running,
            'interval_seconds': self.interval_seconds,
            'next_scheduled_run': self.next_scheduled_run.isoformat() if self.next_scheduled_run else None,
            'last_run_time': self.last_run_time.isoformat() if self.last_run_time else None,
            'success_count': self.success_count,
            'error_count': self.error_count,
            'uptime_seconds': (
                (datetime.utcnow() - self.last_run_time).total_seconds()
                if self.last_run_time and self.is_running else 0
            )
        }

    def update_interval(self, interval_seconds: int) -> None:
        """
        Update the monitoring interval.

        Args:
            interval_seconds: New interval in seconds
        """
        self.interval_seconds = interval_seconds