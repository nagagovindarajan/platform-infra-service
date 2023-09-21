from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import schedule
import time
import threading
from health_checker import HealthChecker

app = FastAPI()

origins = ["*"]
healthChecker = HealthChecker()

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Scheduler:
    def __init__(self):
        self.scheduler_thread = threading.Thread(target=self.run_schedule)
        self.scheduler_thread.start()

    @staticmethod
    def testapi():
        print('Invoking health check job..')
        healthChecker.extract_data('websites_cleaned.csv')
        healthChecker.delete_old_records()
        healthChecker.save_latest_summary()


    def run_schedule(self):
        schedule.every(10).minutes.do(self.testapi)
        while True:
            schedule.run_pending()
            time.sleep(1)
            

@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/latest-summary")
def summary():
    summary = healthChecker.get_latest_summary()
    print('Latest summary', str(summary))
    return summary


@app.get("/websites-status")
def websites_status():
    response = healthChecker.get_websites_status()
    print('Websites status', len(response))
    return response


@app.get("/past-hour-summary")
def past_hour_summary():
    summary = healthChecker.get_past_one_hour_summary()
    print('Past hour summary', len(summary))
    return summary


scheduler = Scheduler()