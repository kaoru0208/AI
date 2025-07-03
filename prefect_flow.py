from prefect import flow
from prefect.deployments import Deployment
from prefect.server.schemas.schedules import CronSchedule
import subprocess
@flow
def daily_train():
    subprocess.run(["python", "train.py"], check=True)
if __name__ == "__main__":
    Deployment.build_from_flow(
        flow=daily_train,
        name="9am-jst",
        work_queue_name="default",
        schedule=CronSchedule(cron="0 0 * * *", timezone="Asia/Tokyo"),
    ).apply()
