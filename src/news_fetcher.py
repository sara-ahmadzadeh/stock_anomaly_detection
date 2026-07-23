# news_fetcher.py
import requests
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class NewsFetcher:
    """
    Fetches crypto news headlines when anomalies occur.
    Uses CryptoPanic free API (no key required for basic usage).
    """
    
    def __init__(self):
        self.base_url = "https://cryptopanic.com/api/v1/posts/"
        self.cache = {}
        self.cache_time = {}
    
    def get_news(self, symbol, limit=3):
        """
        Fetch recent news for a cryptocurrency.
        Returns list of dicts with title, url, and sentiment.
        """
        # Check cache (valid for 10 minutes)
        now = datetime.now()
        if symbol in self.cache and symbol in self.cache_time:
            if (now - self.cache_time[symbol]).seconds < 600:
                return self.cache[symbol]
        
        # Map symbols to search terms
        search_terms = {
            'BTC': 'bitcoin',
            'ETH': 'ethereum',
            'SOL': 'solana',
            'DOGE': 'dogecoin',
            'ADA': 'cardano',
            'XRP': 'ripple',
        }
        
        search = search_terms.get(symbol, symbol.lower())
        
        try:
            params = {
                'currencies': search.upper(),
                'kind': 'news',
                'public': 'true',
            }
            
            response = requests.get(
                self.base_url,
                params=params,
                timeout=10,
                headers={'User-Agent': 'AnomalyDetectionBot/1.0'}
            )
            
            if response.status_code == 200:
                data = response.json()
                headlines = []
                
                for post in data.get('results', [])[:limit]:
                    title = post.get('title', 'No title')
                    url = post.get('url', '#')
                    
                    # If no direct URL, use the CryptoPanic link
                    if not url or url == '#':
                        slug = post.get('slug', '')
                        if slug:
                            url = f"https://cryptopanic.com/news/{slug}"
                    
                    headlines.append({
                        'title': title,
                        'published': post.get('published_at', ''),
                        'url': url,
                        'sentiment': post.get('votes', {}).get('positive', 0) - 
                                    post.get('votes', {}).get('negative', 0)
                    })
                
                self.cache[symbol] = headlines
                self.cache_time[symbol] = now
                return headlines
            # If CryptoPanic fails, use a simple Google News search link
            if not headlines:
                search_term = search_terms.get(symbol, symbol.lower())
                headlines = [{
                    'title': f'Search "{search_term} news" on Google',
                    'url': f'https://www.google.com/search?q={search_term}+crypto+news&tbm=nws',
                    'published': '',
                    'sentiment': 0
                }]
            
            return headlines
            
        except Exception as e:
            logger.warning(f"News fetch failed for {symbol}: {e}")
            return []
    
    def get_market_news(self, limit=3):
        """Fetch general crypto market news."""
        try:
            params = {
                'kind': 'news',
                'public': 'true',
                'filter': 'rising',
            }
            
            response = requests.get(
                self.base_url,
                params=params,
                timeout=10,
                headers={'User-Agent': 'AnomalyDetectionBot/1.0'}
            )
            
            if response.status_code == 200:
                data = response.json()
                headlines = []
                for post in data.get('results', [])[:limit]:
                    title = post.get('title', '')
                    url = post.get('url', '#')
                    slug = post.get('slug', '')
                    if not url and slug:
                        url = f"https://cryptopanic.com/news/{slug}"
                    headlines.append({
                        'title': title,
                        'url': url
                    })
                return headlines
            
            return []
            
        except Exception as e:
            logger.warning(f"Market news failed: {e}")
            return []