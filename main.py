import requests
import time
import json
import os
from tabulate import tabulate
from datetime import datetime, timedelta, timezone
from termcolor import colored

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

class MemeScanner:
    def __init__(self, cmc_api_key, dune_api_key):
        self.cmc_api_key = cmc_api_key
        self.dune_client = DuneClient(dune_api_key)
        self.cmc_headers = {
            'X-CMC_PRO_API_KEY': cmc_api_key,
        }
        print("✅ Scanner initialized with API keys")
    
    def get_token_metadata(self, coin_id, symbol):
        """Fetch detailed metadata for a token"""
        print(f"📡 Fetching metadata for {symbol}...", end='', flush=True)
        url = f'https://pro-api.coinmarketcap.com/v2/cryptocurrency/info'
        params = {'id': coin_id}
        
        try:
            response = requests.get(url, headers=self.cmc_headers, params=params)
            if str(coin_id) not in response.json().get('data', {}):
                raise Exception("Token metadata not found")
            data = response.json()['data'][str(coin_id)]
            
            platform = data.get('platform', {})
            is_solana = platform.get('name', '').lower() == 'solana'
            
            if not is_solana:
                raise Exception("Not a Solana token")
                
            print(f" ✅")
            return {
                'website': data.get('urls', {}).get('website', [''])[0],
                'twitter': data.get('urls', {}).get('twitter', [''])[0],
                'telegram': data.get('urls', {}).get('chat', [''])[0],
                'explorer': data.get('urls', {}).get('explorer', [''])[0],
                'description': data.get('description', '')[:100] + '...' if data.get('description') else 'N/A',
                'platform': platform.get('name', 'N/A'),
                'token_address': platform.get('token_address', 'N/A')
            }
        except Exception as e:
            print(f" ❌")
            return None

    def analyze_with_dune(self, token_address):
        """Get Dune analysis for a token"""
        try:
            QUERY_ID = "4304509"  # Your Dune query ID
            results = self.dune_client.execute_query_and_wait(QUERY_ID, token_address)
            
            if 'result' in results and 'rows' in results['result'] and results['result']['rows']:
                latest_row = results['result']['rows'][0]
                return {
                    'dune_score': latest_row.get('memecoin_score', 'N/A'),
                    'dune_interpretation': latest_row.get('score_interpretation', 'N/A')
                }
        except Exception as e:
            print(f"⚠️ Dune analysis failed for {token_address}: {str(e)}")
        
        return {
            'dune_score': 'N/A',
            'dune_interpretation': 'N/A'
        }

    def scan_memecoins(self, volume_threshold=50000, min_price_increase=20, max_price_increase=300):
        """Scan for trending memecoins and analyze with Dune"""
        print(f"\n🔍 Scanning for Solana memecoins...")
        
        url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest'
        params = {
            'limit': 5000,
            'convert': 'USD',
            'sort': 'percent_change_24h',
            'sort_dir': 'desc',
            'cryptocurrency_type': 'tokens'
        }
        
        try:
            response = requests.get(url, headers=self.cmc_headers, params=params)
            data = response.json()['data']
        except Exception as e:
            print(f"❌ Error fetching CMC data: {str(e)}")
            return []
        
        trending_coins = []
        current_time = datetime.now(timezone.utc)
        
        for coin in data:
            quote = coin['quote']['USD']
            price_change = quote['percent_change_24h']
            
            if (quote['volume_24h'] > volume_threshold and
                min_price_increase <= price_change <= max_price_increase and
                datetime.fromisoformat(coin['date_added'].replace('Z', '+00:00')) > current_time - timedelta(days=30)):
                
                metadata = self.get_token_metadata(coin['id'], coin['symbol'])
                if metadata:
                    # Get Dune analysis
                    dune_results = self.analyze_with_dune(metadata['token_address'])
                    
                    coin_data = {
                        'symbol': coin['symbol'],
                        'name': coin['name'],
                        'price_change_24h': price_change,
                        'volume_24h': quote['volume_24h'],
                        'volume_change_24h': quote.get('volume_change_24h', 0),
                        'market_cap': quote.get('market_cap', 0),
                        'price': quote['price'],
                        'date_added': coin['date_added'],
                        **metadata,
                        **dune_results
                    }
                    
                    trending_coins.append(coin_data)
                    print(f"\n💫 Found: {coin['symbol']}")
                    print(f"   Price Change: {price_change:.2f}%")
                    print(f"   Volume Change: {coin_data['volume_change_24h']:.2f}%")
                    print(f"   Market Cap: ${coin_data['market_cap']:,.2f}")  # Added market cap display
                    print(f"   Dune Score: {dune_results['dune_score']}")
                    print(f"   Signal: {dune_results['dune_interpretation']}")
                
                time.sleep(0.2)  # Rate limiting
        
        return trending_coins

    def format_results(self, coins):
        """Format results with both CMC and Dune data, including full address and volume change"""
        if not coins:
            print("\n❌ No trending tokens found")
            return
            
        # Sort by Dune score and price change
        coins.sort(key=lambda x: (
            float(x['dune_score']) if isinstance(x['dune_score'], (int, float)) else -1,
            x['price_change_24h']
        ), reverse=True)
        
        # Prepare table data
        table_data = []
        for coin in coins:
            # Format price change
            price_change = f"{coin['price_change_24h']:+.2f}%"
            
            # Format volume and volume change
            volume = "${:,.2f}M".format(coin['volume_24h'] / 1e6)
            volume_change = f"{coin['volume_change_24h']:+.2f}%" if coin['volume_change_24h'] else "N/A"
            
            # Format market cap
            market_cap = "${:,.2f}M".format(coin['market_cap'] / 1e6)
            
            # Format Dune score
            dune_score = coin['dune_score']
            
            row = [
                coin['symbol'],
                coin['name'][:15] + '...',
                colored(price_change, 'green' if coin['price_change_24h'] > 0 else 'red'),
                volume,
                colored(volume_change, 'green' if coin.get('volume_change_24h', 0) > 0 else 'red'),
                market_cap,  # Added market cap column
                str(dune_score),
                coin['dune_interpretation'],
                coin['token_address']
            ]
            table_data.append(row)
        
        # Print results
        headers = ['Symbol', 'Name', 'Price 24h', 'Volume', 'Vol Change', 'Market Cap', 'Dune Score', 'Signal', 'Token Address']  # Added Market Cap header
        print("\n" + "="*80)
        print(colored("🚀 TRENDING SOLANA MEMECOINS WITH DUNE ANALYSIS 🚀", 'yellow', attrs=['bold']))
        print("="*80 + "\n")
        print(tabulate(table_data, headers=headers, tablefmt='simple'))
        
        # Print detailed info for top 5
        print("\n" + "="*40)
        print(colored("🔥 TOP 5 DETAILED VIEW 🔥", 'yellow', attrs=['bold']))
        print("="*40)
        
        for i, coin in enumerate(coins[:5], 1):
            price_change_color = 'green' if coin['price_change_24h'] > 0 else 'red'
            volume_change_color = 'green' if coin.get('volume_change_24h', 0) > 0 else 'red'
            
            print(f"\n{colored(f'#{i}', 'cyan', attrs=['bold'])} {colored(coin['symbol'], 'yellow', attrs=['bold'])} - {coin['name']}")
            print("="*50)
            
            price_change_str = f"{coin['price_change_24h']:+.2f}%"
            volume_change_str = f"{coin['volume_change_24h']:+.2f}%"
            
            print(f"Price Change: {colored(price_change_str, price_change_color)}")
            print(f"Volume: ${coin['volume_24h']:,.2f}")
            print(f"Volume Change: {colored(volume_change_str, volume_change_color)}")
            print(f"Market Cap: ${coin['market_cap']:,.2f}")  # Added market cap display
            print(f"Dune Score: {colored(str(coin['dune_score']), 'cyan')}")
            print(f"Signal: {colored(coin['dune_interpretation'], 'yellow')}")
            print(f"\nToken Address: {colored(coin['token_address'], 'blue')}")
            
            if coin['twitter']:
                print(f"Twitter: {coin['twitter']}")
            if coin['telegram']:
                print(f"Telegram: {coin['telegram']}")
            print(f"Explorer: {coin['explorer']}")
            print("="*50)

def main():
    print("🚀 Starting Combined Memecoin Scanner...")
    
    # Check for API keys
    cmc_api_key = os.getenv('CMC_TOKEN')
    dune_api_key = os.getenv('DUNE_TOKEN')
    
    if not cmc_api_key or not dune_api_key:
        print("❌ Error: Please set both CMC_TOKEN and DUNE_TOKEN environment variables")
        return
    
    try:
        scanner = MemeScanner(cmc_api_key, dune_api_key)
        trending = scanner.scan_memecoins(
            volume_threshold=50000,
            min_price_increase=20,
            max_price_increase=300
        )
        scanner.format_results(trending)
        print("\n✨ Scan completed successfully!")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")

if __name__ == '__main__':
    main()
