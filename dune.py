import requests
import time
import json

class DuneClient:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.dune.com/api/v1"
        self.headers = {
            "X-Dune-API-Key": self.api_key,
            "Content-Type": "application/json"
        }

    def execute_query(self, query_id, token_address):
        url = f"{self.base_url}/query/{query_id}/execute"
        parameters = {
            "query_parameters": {
                "token_address": token_address
            }
        }
        try:
            response = requests.post(url, headers=self.headers, json=parameters)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            if hasattr(e.response, 'text'):
                print(f"Response content: {e.response.text}")
            raise

    def get_execution_status(self, execution_id):
        url = f"{self.base_url}/execution/{execution_id}/status"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def get_execution_result(self, execution_id):
        url = f"{self.base_url}/execution/{execution_id}/results"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def execute_query_and_wait(self, query_id, token_address, max_retries=50, sleep_time=5):
        try:
            execution = self.execute_query(query_id, token_address)
            execution_id = execution['execution_id']

            for _ in range(max_retries):
                status = self.get_execution_status(execution_id)
                state = status.get('state', 'UNKNOWN')
                
                if state == 'QUERY_STATE_COMPLETED':
                    return self.get_execution_result(execution_id)
                elif state == 'QUERY_STATE_FAILED':
                    raise Exception("Query failed")
                elif state == 'QUERY_STATE_CANCELLED':
                    raise Exception("Query was cancelled")
                
                time.sleep(sleep_time)
                
            raise TimeoutError("Query execution timed out")
            
        except Exception as e:
            raise

if __name__ == "__main__":
    API_KEY = os.getenv('DUNE_TOKEN')
    QUERY_ID = "4304509"
    TOKEN_ADDRESS = "9TY6DUg1VSssYH5tFE95qoq5hnAGFak4w3cn72sJNCoV"
    
    client = DuneClient(API_KEY)
    
    try:
        results = client.execute_query_and_wait(QUERY_ID, TOKEN_ADDRESS)
        
        if 'result' in results and 'rows' in results['result']:
            rows = results['result']['rows']
            if rows:
                latest_row = rows[0]
                print(f"Score Interpretation: {latest_row['score_interpretation']}")
                print(f"Memecoin Score: {latest_row['memecoin_score']}")
        else:
            print("No results found")
            
    except Exception as e:
        print(f"Error: {str(e)}")
