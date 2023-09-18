from health_checker import HealthChecker

#This file Only for local testing

def test_health_check_job():
    healthChecker = HealthChecker() 
    healthChecker.extract_data('testfile.csv')
    healthChecker.delete_old_records()
    healthChecker.save_latest_summary()

def test_past_one_hour_summary():
    healthChecker = HealthChecker() 
    response = healthChecker.get_past_one_hour_summary()
    print("Past one hour response ", response)

def test_latest_summary():
    healthChecker = HealthChecker() 
    response = healthChecker.get_latest_summary()
    print("latest_summary response ", response)

def test_websites_status():
    healthChecker = HealthChecker() 
    response = healthChecker.get_websites_status()
    print("websites_status response ", response)


def main():
    # test_health_check_job()
    test_past_one_hour_summary()
    # test_latest_summary()
    # test_websites_status()

if __name__ == "__main__":
    main()