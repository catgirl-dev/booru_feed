from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore

def create_scheduler():
    return AsyncIOScheduler(
    jobstores={
        'default': SQLAlchemyJobStore(
            url='sqlite:///fetcher_info.db'
        )
    }
)
