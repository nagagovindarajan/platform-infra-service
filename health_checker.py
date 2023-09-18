import csv
import json
from urllib.parse import urlparse
import requests
import time
import threading
from collections import defaultdict
import boto3
from datetime import datetime

website_status = {}
lock = threading.Lock()
table_name = 'platform-eng'
region_name='ap-southeast-1'

class HealthChecker:

    def __init__(self):
        self.dynamodb = boto3.client("dynamodb", region_name=region_name)
        self.dynamodb_resource = boto3.resource('dynamodb', region_name=region_name)
        print('Initialise Dynamo DB')

    def process_row(self, row):
        website_url = row['website_url']
        category = row['Category']
        parsed_url = urlparse(website_url)
        domain = parsed_url.netloc
        # print(f"Thread-{threading.current_thread().name} reading URL {domain}")

        try:
            r = requests.head(website_url, timeout=5)
            status_code = r.status_code

        except requests.exceptions.Timeout:
            status_code = 408

        except Exception as e:
            status_code = 500
        
        with lock:
            website_status[domain] = {
                'name': domain,
                'Category': category,
                'Status': status_code
            }

    def extract_data(self, file_path):
        start_time = time.time()
        rows = []

        with open(file_path, mode='r') as file:
            csv_reader = csv.DictReader(file)
            rows = [row for row in csv_reader]

        threads = []

        for i in range(10):  # 10 threads
            # Create a thread that will process a subset of rows
            t = threading.Thread(target=lambda: [self.process_row(row) for row in rows[i::10]], name=f"{i}")
            threads.append(t)
            t.start()

        # Wait for all threads to finish
        for t in threads:
            t.join()

        print("All threads have finished.")

        print('writing status')
        with open('website_status.json', 'w') as json_file:
            json.dump(website_status, json_file, indent=4)

        print("Website statuses have been saved to website_status.json.")
        
        end_time = time.time()
        execution_duration = end_time - start_time
        print(f"Execution Duration: {execution_duration} seconds")

    def get_websites_status(self):
        
        with open('website_status.json', 'r') as file:
            data = json.load(file)

        return data
    
    def get_latest_summary(self):

        data = self.get_websites_status()

        status_count = defaultdict(int)

        for key, value in data.items():
            status = value['Status']
            status_count[status] += 1

        output_data = dict(status_count)

        return output_data
    
    def get_past_one_hour_summary(self):
        table = self.dynamodb_resource.Table(table_name)
        response = table.scan()
        items = response['Items']
        sorted_items = sorted(items, key=lambda x: int(x['id']), reverse=True)
        result = []
        for past_hour_item in sorted_items:
            summary_obj = json.loads(past_hour_item.get('summary'))
            time_stamp = datetime.fromtimestamp(past_hour_item.get('id')/1000).strftime('%Y-%m-%d %H:%M:%S')
            summary_obj["time_stamp"] = time_stamp
            result.append(summary_obj)
        
        return result


    def delete_old_records(self):
        table = self.dynamodb_resource.Table(table_name)
        one_hour_ago = int((time.time() - 3600) * 1000)  # 3600 seconds = 1 hour
        items = self.get_past_one_hour_summary()

        if len(items) > 0:
            # Delete each item that is older than one hour
            print(f"Deleting older items")
            for item in items:
                if int(item['id']) < one_hour_ago:
                    table.delete_item(
                        Key={
                            'id': item['id']
                        }
                    )

            print("Delete operation completed")


    def save_latest_summary(self):
        latest_summary = self.get_latest_summary()
        print('Storing summary into dynamodb table '+table_name)
        unique_timestamp = int(time.time() * 1000)  # Milliseconds since epoch

        response = self.dynamodb.put_item(
            TableName = table_name,
            Item={
                'id': {'N': str(unique_timestamp)},
                'summary': {'S': json.dumps(latest_summary)}
            }
        )

        print("Dynamo DB resposne ", response)
    
