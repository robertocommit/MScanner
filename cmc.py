import requests
from tabulate import tabulate
from datetime import datetime, timedelta, timezone
from termcolor import colored
import time
import os

api_key = "INSERT_YOUR_API"

class MemeScanner:
    def __init__(self, api_key):
        self.api_key = api_key
        self.headers = {
            'X-CMC_PRO_API_KEY': api_key,
        }
        print("✅ Scanner initialized with API key")
    
    def get_token_metadata(self, coin_id, symbol):
        """Fetch detailed metadata for a token"""
        print(f"📡 Fetching metadata for {symbol}...", end='', flush=True)
        url = f'https://pro-api.coinmarketcap.com/v2/cryptocurrency/info'
        params = {'id': coin_id}
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            if str(coin_id) not in response.json().get('data', {}):
                raise Exception("Token metadata not found")
            data = response.json()['data'][str(coin_id)]
            
            # Check if token is on Solana
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

    def scan_memecoins(self, volume_threshold=50000, min_price_increase=20, max_price_increase=300):
        """Scan for trending memecoins with enhanced data"""
        print(f"\n🔍 Scanning for Solana memecoins with:")
        print(f"   - Minimum volume: ${volume_threshold:,}")
        print(f"   - 24h growth range: {min_price_increase}% to {max_price_increase}%")
        
        print("\n📊 Fetching latest market data from CMC...", end='', flush=True)
        url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest'
        params = {
            'limit': 5000,
            'convert': 'USD',
            'sort': 'percent_change_24h',
            'sort_dir': 'desc',
            'cryptocurrency_type': 'tokens'
        }
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            data = response.json()['data']
            print(" ✅")
            print(f"📈 Processing {len(data)} tokens...")
        except Exception as e:
            print(f" ❌\nError fetching data: {str(e)}")
            return []
        
        trending_coins = []
        matches_found = 0
        current_time = datetime.now(timezone.utc)
        
        for index, coin in enumerate(data):
            quote = coin['quote']['USD']
            price_change = quote['percent_change_24h']
            volume_change = quote.get('volume_change_24h', 0)
            
            # Convert date_added to UTC for comparison
            coin_date = datetime.fromisoformat(coin['date_added'].replace('Z', '+00:00'))
            
            if (quote['volume_24h'] > volume_threshold and
                min_price_increase <= price_change <= max_price_increase and
                coin_date > current_time - timedelta(days=30)):
                
                matches_found += 1
                print(f"\n🎯 Found potential memecoin #{matches_found}: {coin['symbol']}")
                print(f"   Price change: {price_change:.2f}%")
                print(f"   Volume: ${quote['volume_24h']:,.2f}")
                
                # Get additional metadata and check if it's a Solana token
                metadata = self.get_token_metadata(coin['id'], coin['symbol'])
                if metadata:  # Only add if it's a Solana token
                    time.sleep(0.2)  # Respect API rate limits
                    
                    trending_coins.append({
                        'symbol': coin['symbol'],
                        'name': coin['name'],
                        'price_change_24h': price_change,
                        'volume_24h': quote['volume_24h'],
                        'volume_change_24h': volume_change,
                        'market_cap': quote.get('market_cap', 0),
                        'price': quote['price'],
                        'date_added': coin['date_added'],
                        **metadata
                    })
            
            # Progress indicator every 1000 tokens
            if (index + 1) % 1000 == 0:
                print(f"⏳ Processed {index + 1} tokens...")
        
        print(f"\n✨ Scan complete! Found {len(trending_coins)} trending Solana memecoins")
        return trending_coins

    def format_results(self, coins):
        """Format results in a clean table"""
        if not coins:
            print("\n❌ No trending Solana memecoins found matching criteria")
            return
            
        print("\n📊 Formatting results...")
        
        # Sort coins by price change first
        coins.sort(key=lambda x: x['price_change_24h'], reverse=True)
        
        formatted_data = []
        for coin in coins:
            # Format price and volume changes
            price_change = coin['price_change_24h']
            volume_change = coin['volume_change_24h']
            
            price_str = f"+{price_change:.2f}%" if price_change > 0 else f"{price_change:.2f}%"
            volume_str = f"+{volume_change:.2f}%" if volume_change > 0 else f"{volume_change:.2f}%"
            
            colored_price = colored(price_str, 'green' if price_change > 0 else 'red')
            colored_volume = colored(volume_str, 'green' if volume_change > 0 else 'red')
            
            # Format numbers
            def format_number(num):
                if num >= 1e9:
                    return f"${num/1e9:.2f}B"
                elif num >= 1e6:
                    return f"${num/1e6:.2f}M"
                else:
                    return f"${num/1e3:.2f}K"
            
            # Format date
            date = datetime.fromisoformat(coin['date_added'].replace('Z', '+00:00'))
            days_ago = (datetime.now(timezone.utc) - date).days
            
            volume_formatted = format_number(coin['volume_24h'])
            mcap_formatted = format_number(coin.get('market_cap', 0))
            
            formatted_data.append([
                coin['symbol'],
                coin['name'][:20] + ('...' if len(coin['name']) > 20 else ''),
                colored_price,
                colored_volume,
                volume_formatted,
                mcap_formatted,
                f"${coin['price']:.8f}",
                f"{days_ago}d ago",
                coin['token_address'][:8] + '...',
                coin['twitter'].replace('https://twitter.com/', '@'),
                coin['telegram']
            ])
        
        # Print main table
        headers = ['Symbol', 'Name', 'Price 24h', 'Vol 24h%', 'Volume', 'MCap', 'Price', 'Listed', 'Address', 'Twitter', 'Telegram']
        print("\n" + "="*10)
        print(colored("🚀 TRENDING SOLANA MEMECOINS 🚀", 'yellow', attrs=['bold']).center(10))
        print("="*10 + "\n")
        print(tabulate(formatted_data, headers=headers, tablefmt='simple'))
        
        # Print detailed info for top 5 with enhanced formatting
        print("\n" + "="*10)
        print(colored("🔥 TOP 5 TRENDING SOLANA MEMECOINS 🔥", 'yellow', attrs=['bold']).center(10))
        print("="*10)
        
        for i, coin in enumerate(coins[:5]):
            print("\n" + colored(f"{'='*4} #{i+1} {'='*4}", 'blue'))
            name_header = f"{coin['symbol']} - {coin['name']}"
            print(colored(name_header.center(10), 'cyan', attrs=['bold']))
            
            # Format metrics with colors and emojis
            price_change_str = f"{coin['price_change_24h']:+.2f}%"
            volume_change_str = f"{coin['volume_change_24h']:+.2f}%"
            volume_str = "${:,.2f}".format(coin['volume_24h'])
            mcap_str = "${:,.2f}".format(coin.get('market_cap', 0))
            
            # Print metrics in a centered, organized way
            print("\n" + colored("📊 METRICS", 'yellow', attrs=['bold']).center(10))
            print(f"{'Price Change (24h):':<30} {colored(price_change_str, 'green' if coin['price_change_24h'] > 0 else 'red')}")
            print(f"{'Volume Change (24h):':<30} {colored(volume_change_str, 'green' if coin['volume_change_24h'] > 0 else 'red')}")
            print(f"{'Volume:':<30} {colored(volume_str, 'blue')}")
            print(f"{'Market Cap:':<30} {colored(mcap_str, 'blue')}")
            
            # Links section
            print("\n" + colored("🔗 LINKS", 'yellow', attrs=['bold']).center(10))
            print(f"{'Explorer:':<15} {colored(coin['explorer'], 'blue')}")
            print(f"{'Token:':<15} {colored(coin['token_address'], 'blue')}")
            if coin['twitter']:
                print(f"{'Twitter:':<15} {colored(coin['twitter'], 'blue')}")
            if coin['telegram']:
                print(f"{'Telegram:':<15} {colored(coin['telegram'], 'blue')}")
            
            print(colored("="*10, 'blue'))

def main():
    print("🚀 Starting Solana Memecoin Scanner...")
    
    # Check for API key
    cmc_api_key = os.getenv('CMC_TOKEN')
    # cmc_api_key = api_key
    if not cmc_api_key:
        print("❌ Error: Please set your CMC_TOKEN environment variable")
        exit(1)
    
    try:
        scanner = MemeScanner(cmc_api_key)
        trending = scanner.scan_memecoins(
            volume_threshold=50000,
            min_price_increase=20,
            max_price_increase=300
        )
        scanner.format_results(trending)
        print("\n✨ Scan completed successfully!")
    except Exception as e:
        print(f"\n❌ Error during execution: {str(e)}")
        raise

if __name__ == '__main__':
    main()
