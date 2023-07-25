import asyncio

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from damai.performer import ApiFetchPerform

ARGS = (721234813852, 5190876482301, 1)
TRIGGER = dict(hour=10, minute=59, second=59)


def main():
    loop = asyncio.get_event_loop()
    scheduler = AsyncIOScheduler(timezone='Asia/Shanghai')
    instant = ApiFetchPerform()
    instant.update_default_config(dict(COOKIE=''))
    scheduler.add_job(instant.submit, "cron", args=ARGS, **TRIGGER)
    scheduler.start()
    try:
        loop.run_forever()
    except (KeyboardInterrupt, SystemExit):
        pass


main()
