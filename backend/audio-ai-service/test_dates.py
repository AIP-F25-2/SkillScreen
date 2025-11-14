"""
Test performance metrics directly
"""
import sys
sys.path.append('/common-service')

from db import UnitOfWork
from monitoring.metrics import MetricsCollector
from datetime import datetime, timedelta, timezone as tz

uow = UnitOfWork()
collector = MetricsCollector(uow.session)

date_threshold = datetime.now(tz.utc) - timedelta(days=30)

print("Testing performance metrics...")
perf = collector._get_performance_metrics(date_threshold, None)

print(f"\nResults:")
print(f"  total_processed: {perf['total_processed']}")
print(f"  processing_time: {perf['processing_time']}")
print(f"  status_breakdown: {perf['status_breakdown']}")