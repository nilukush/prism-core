"""
Advanced DDoS protection middleware with multiple defense layers.
"""

import os
import time
import asyncio
import ipaddress
from typing import Dict, Set, Optional, List, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, deque
import hashlib
import hmac
import secrets

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse, HTMLResponse
from redis import asyncio as aioredis
import httpx

from backend.src.core.config import settings
from backend.src.core.logging import logger
from backend.src.core.telemetry import trace_async, metrics

# Metrics
ddos_blocks = metrics.counter(
    "ddos_blocks_total",
    "Total number of DDoS blocks",
    ["defense_layer", "reason"]
)

ddos_challenges = metrics.counter(
    "ddos_challenges_total",
    "Total number of DDoS challenges issued",
    ["challenge_type"]
)

traffic_anomalies = metrics.counter(
    "traffic_anomalies_total",
    "Total number of traffic anomalies detected",
    ["anomaly_type"]
)


class TrafficAnalyzer:
    """Analyzes traffic patterns for anomaly detection."""
    
    def __init__(self, window_size: int = 300):  # 5 minutes
        self.window_size = window_size
        self.request_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.baseline_stats: Dict[str, Dict] = {}
        
    def record_request(self, client_ip: str, request: Request):
        """Record request for analysis."""
        now = time.time()
        self.request_history[client_ip].append({
            "timestamp": now,
            "path": request.url.path,
            "method": request.method,
            "size": int(request.headers.get("Content-Length", 0)),
            "user_agent": request.headers.get("User-Agent", "")
        })
    
    def detect_anomalies(self, client_ip: str) -> List[str]:
        """Detect traffic anomalies for a client."""
        anomalies = []
        history = self.request_history.get(client_ip, [])
        
        if len(history) < 10:
            return anomalies
        
        now = time.time()
        recent_requests = [r for r in history if now - r["timestamp"] < self.window_size]
        
        # Detect request flooding
        if len(recent_requests) > 100:
            anomalies.append("request_flooding")
            traffic_anomalies.inc({"anomaly_type": "request_flooding"})
        
        # Detect path scanning
        unique_paths = set(r["path"] for r in recent_requests)
        if len(unique_paths) > 50:
            anomalies.append("path_scanning")
            traffic_anomalies.inc({"anomaly_type": "path_scanning"})
        
        # Detect abnormal request patterns
        if self._detect_pattern_anomaly(recent_requests):
            anomalies.append("pattern_anomaly")
            traffic_anomalies.inc({"anomaly_type": "pattern_anomaly"})
        
        return anomalies
    
    def _detect_pattern_anomaly(self, requests: List[Dict]) -> bool:
        """Detect abnormal request patterns using statistical analysis."""
        if len(requests) < 20:
            return False
        
        # Calculate inter-request times
        timestamps = sorted(r["timestamp"] for r in requests)
        intervals = [timestamps[i+1] - timestamps[i] for i in range(len(timestamps)-1)]
        
        if not intervals:
            return False
        
        # Check for suspiciously regular intervals (bot behavior)
        avg_interval = sum(intervals) / len(intervals)
        variance = sum((i - avg_interval) ** 2 for i in intervals) / len(intervals)
        
        # Low variance indicates bot-like behavior
        if variance < 0.1 and avg_interval < 1.0:
            return True
        
        return False


class GeoIPFilter:
    """Geographic IP filtering for DDoS protection."""
    
    def __init__(self, redis_client: aioredis.Redis):
        self.redis = redis_client
        self.blocked_countries: Set[str] = set()
        self.allowed_countries: Set[str] = set()
        self.high_risk_countries: Set[str] = {"CN", "RU", "KP", "IR"}  # Example
        
    async def check_geo_restrictions(self, ip: str) -> Tuple[bool, Optional[str]]:
        """
        Check if IP is allowed based on geographic restrictions.
        Returns (allowed, country_code)
        """
        # Check cache first
        cache_key = f"geoip:{ip}"
        cached_country = await self.redis.get(cache_key)
        
        if cached_country:
            country = cached_country
        else:
            # In production, use a GeoIP service like MaxMind
            country = await self._lookup_country(ip)
            await self.redis.setex(cache_key, 86400, country or "XX")  # Cache for 24 hours
        
        # Check restrictions
        if self.allowed_countries and country not in self.allowed_countries:
            return False, country
        
        if country in self.blocked_countries:
            return False, country
        
        return True, country
    
    async def _lookup_country(self, ip: str) -> Optional[str]:
        """Look up country code for IP address."""
        # In production, integrate with MaxMind GeoIP2 or similar
        # For now, return None for private IPs
        try:
            ip_obj = ipaddress.ip_address(ip)
            if ip_obj.is_private or ip_obj.is_loopback:
                return "LOCAL"
        except ValueError:
            pass
        
        return None
    
    def is_high_risk_country(self, country_code: Optional[str]) -> bool:
        """Check if country is considered high risk."""
        return country_code in self.high_risk_countries


class ChallengeResponse:
    """Implements challenge-response mechanisms for bot detection."""
    
    def __init__(self, redis_client: aioredis.Redis):
        self.redis = redis_client
        self.challenge_secret = settings.SECRET_KEY.encode()
    
    def generate_challenge(self, client_ip: str) -> Dict[str, str]:
        """Generate a challenge for the client."""
        challenge_id = secrets.token_urlsafe(32)
        timestamp = str(int(time.time()))
        
        # Create challenge data
        challenge_data = f"{challenge_id}:{client_ip}:{timestamp}"
        signature = hmac.new(
            self.challenge_secret,
            challenge_data.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return {
            "challenge_id": challenge_id,
            "timestamp": timestamp,
            "signature": signature
        }
    
    async def verify_challenge(self, client_ip: str, challenge_response: Dict) -> bool:
        """Verify a challenge response."""
        try:
            challenge_id = challenge_response.get("challenge_id")
            timestamp = challenge_response.get("timestamp")
            signature = challenge_response.get("signature")
            solution = challenge_response.get("solution")
            
            if not all([challenge_id, timestamp, signature, solution]):
                return False
            
            # Verify signature
            challenge_data = f"{challenge_id}:{client_ip}:{timestamp}"
            expected_signature = hmac.new(
                self.challenge_secret,
                challenge_data.encode(),
                hashlib.sha256
            ).hexdigest()
            
            if not hmac.compare_digest(signature, expected_signature):
                return False
            
            # Check timestamp (5 minute window)
            if abs(int(timestamp) - int(time.time())) > 300:
                return False
            
            # Check if challenge was already used
            used_key = f"challenge_used:{challenge_id}"
            if await self.redis.exists(used_key):
                return False
            
            # Mark challenge as used
            await self.redis.setex(used_key, 3600, "1")
            
            # In a real implementation, verify the actual solution
            # For now, accept any non-empty solution
            return bool(solution)
            
        except Exception as e:
            logger.error(f"Challenge verification error: {e}")
            return False
    
    def generate_javascript_challenge(self) -> str:
        """Generate a JavaScript challenge for browser verification."""
        challenge = self.generate_challenge("browser")
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Security Check</title>
            <style>
                body {{ font-family: Arial, sans-serif; text-align: center; padding: 50px; }}
                .container {{ max-width: 400px; margin: 0 auto; }}
                .spinner {{ border: 3px solid #f3f3f3; border-top: 3px solid #3498db;
                           border-radius: 50%; width: 40px; height: 40px;
                           animation: spin 1s linear infinite; margin: 20px auto; }}
                @keyframes spin {{ 0% {{ transform: rotate(0deg); }} 
                                  100% {{ transform: rotate(360deg); }} }}
            </style>
        </head>
        <body>
            <div class="container">
                <h2>Security Check</h2>
                <p>Please wait while we verify your browser...</p>
                <div class="spinner"></div>
            </div>
            <script>
                // Solve a simple computational challenge
                function solveChallenge() {{
                    const challenge = {challenge};
                    const start = Date.now();
                    
                    // Simple proof of work
                    let nonce = 0;
                    let solution = '';
                    while (true) {{
                        const attempt = challenge.challenge_id + ':' + nonce;
                        const hash = btoa(attempt);
                        if (hash.startsWith('AA')) {{
                            solution = nonce.toString();
                            break;
                        }}
                        nonce++;
                        
                        // Timeout after 5 seconds
                        if (Date.now() - start > 5000) {{
                            solution = 'timeout';
                            break;
                        }}
                    }}
                    
                    // Submit solution
                    const form = document.createElement('form');
                    form.method = 'POST';
                    form.action = window.location.href;
                    
                    const fields = {{
                        challenge_id: challenge.challenge_id,
                        timestamp: challenge.timestamp,
                        signature: challenge.signature,
                        solution: solution
                    }};
                    
                    for (const [key, value] of Object.entries(fields)) {{
                        const input = document.createElement('input');
                        input.type = 'hidden';
                        input.name = key;
                        input.value = value;
                        form.appendChild(input);
                    }}
                    
                    document.body.appendChild(form);
                    form.submit();
                }}
                
                // Start solving after a short delay
                setTimeout(solveChallenge, 100);
            </script>
        </body>
        </html>
        """.replace("{challenge}", str(challenge))


class DDoSProtection:
    """
    Comprehensive DDoS protection with multiple defense layers.
    """
    
    def __init__(self, redis_url: str = None):
        self.redis_url = redis_url or settings.REDIS_URL
        self.redis: Optional[aioredis.Redis] = None
        self.traffic_analyzer = TrafficAnalyzer()
        self.geo_filter: Optional[GeoIPFilter] = None
        self.challenge_response: Optional[ChallengeResponse] = None
        self.whitelist: Set[str] = set()
        self.blacklist: Set[str] = set()
        self._init_lock = asyncio.Lock()
        
    async def initialize(self):
        """Initialize Redis and components."""
        async with self._init_lock:
            if self.redis is None:
                try:
                    # Use Upstash REST URL if available
                    upstash_url = os.getenv("UPSTASH_REDIS_REST_URL")
                    upstash_token = os.getenv("UPSTASH_REDIS_REST_TOKEN")
                    
                    if upstash_url and upstash_token:
                        # For Upstash, construct Redis URL from REST credentials
                        # Extract host from REST URL
                        import re
                        match = re.search(r'https://([^.]+)\.upstash\.io', upstash_url)
                        if match:
                            host = f"{match.group(1)}.upstash.io"
                            # Use rediss:// for SSL connection
                            redis_url = f"rediss://default:{upstash_token}@{host}:6379"
                        else:
                            redis_url = str(self.redis_url)
                    else:
                        redis_url = str(self.redis_url)
                    
                    # Convert redis:// to rediss:// for Upstash SSL connections
                    if "upstash" in redis_url and redis_url.startswith("redis://"):
                        redis_url = redis_url.replace("redis://", "rediss://", 1)
                    
                    self.redis = await aioredis.from_url(
                        redis_url,
                        encoding="utf-8",
                        decode_responses=True
                    )
                    
                    self.geo_filter = GeoIPFilter(self.redis)
                    self.challenge_response = ChallengeResponse(self.redis)
                    
                    # Load whitelist/blacklist from Redis
                    await self._load_ip_lists()
                except Exception as e:
                    logger.error(f"Failed to connect to Redis for DDoS protection: {e}")
                    logger.warning("DDoS protection disabled due to Redis connection failure")
                    # Continue without Redis - DDoS protection will be limited
                    self.geo_filter = None
                    self.challenge_response = None
    
    async def _load_ip_lists(self):
        """Load IP whitelist and blacklist from Redis."""
        if self.redis:
            whitelist_members = await self.redis.smembers("ddos:whitelist")
            self.whitelist = set(whitelist_members)
            
            blacklist_members = await self.redis.smembers("ddos:blacklist")
            self.blacklist = set(blacklist_members)
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract real client IP considering proxies."""
        # Trust X-Forwarded-For if behind proxy
        if settings.BEHIND_PROXY:
            if forwarded_for := request.headers.get("X-Forwarded-For"):
                return forwarded_for.split(",")[0].strip()
            if real_ip := request.headers.get("X-Real-IP"):
                return real_ip
        
        return request.client.host
    
    @trace_async("ddos_protection_check")
    async def check_request(self, request: Request) -> Optional[JSONResponse]:
        """
        Check request for DDoS patterns and apply protection.
        Returns response if request should be blocked/challenged, None if allowed.
        """
        if self.redis is None:
            await self.initialize()
        
        client_ip = self._get_client_ip(request)
        
        # Layer 1: Whitelist check
        if client_ip in self.whitelist:
            return None
        
        # Layer 2: Blacklist check
        if client_ip in self.blacklist:
            ddos_blocks.inc({"defense_layer": "blacklist", "reason": "ip_blacklisted"})
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"error": "Access denied"}
            )
        
        # Layer 3: Geographic restrictions
        if self.geo_filter:
            allowed, country = await self.geo_filter.check_geo_restrictions(client_ip)
            if not allowed:
                ddos_blocks.inc({"defense_layer": "geo_filter", "reason": f"country_{country}"})
                return JSONResponse(
                    status_code=status.HTTP_403_FORBIDDEN,
                    content={"error": "Access denied from your region"}
                )
        
        # Layer 4: Traffic pattern analysis
        self.traffic_analyzer.record_request(client_ip, request)
        anomalies = self.traffic_analyzer.detect_anomalies(client_ip)
        
        if anomalies:
            # High risk country + anomalies = immediate block
            if self.geo_filter.is_high_risk_country(country):
                ddos_blocks.inc({"defense_layer": "traffic_analysis", "reason": "high_risk_anomaly"})
                await self._add_to_blacklist(client_ip, duration=3600)
                return JSONResponse(
                    status_code=status.HTTP_403_FORBIDDEN,
                    content={"error": "Suspicious activity detected"}
                )
            
            # Otherwise, issue challenge
            if "X-Challenge-Solution" not in request.headers:
                ddos_challenges.inc({"challenge_type": "javascript"})
                return HTMLResponse(
                    content=self.challenge_response.generate_javascript_challenge(),
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE
                )
        
        # Layer 5: Challenge verification if provided
        if "X-Challenge-Solution" in request.headers:
            challenge_data = {
                "challenge_id": request.headers.get("X-Challenge-ID"),
                "timestamp": request.headers.get("X-Challenge-Timestamp"),
                "signature": request.headers.get("X-Challenge-Signature"),
                "solution": request.headers.get("X-Challenge-Solution")
            }
            
            if not await self.challenge_response.verify_challenge(client_ip, challenge_data):
                ddos_blocks.inc({"defense_layer": "challenge", "reason": "invalid_solution"})
                return JSONResponse(
                    status_code=status.HTTP_403_FORBIDDEN,
                    content={"error": "Invalid challenge solution"}
                )
        
        # Layer 6: Connection limit per IP
        if self.redis:
            conn_key = f"ddos:connections:{client_ip}"
            connections = await self.redis.incr(conn_key)
            await self.redis.expire(conn_key, 60)
            
            if connections > 100:  # Max 100 connections per minute
                ddos_blocks.inc({"defense_layer": "connection_limit", "reason": "too_many_connections"})
                return JSONResponse(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    content={"error": "Too many connections"},
                    headers={"Retry-After": "60"}
                )
        
        # Request allowed
        return None
    
    async def _add_to_blacklist(self, ip: str, duration: int = 3600):
        """Add IP to temporary blacklist."""
        if self.redis:
            await self.redis.sadd("ddos:blacklist", ip)
            await self.redis.setex(f"ddos:blacklist:{ip}", duration, "1")
            
            # Clean up after duration
            asyncio.create_task(self._remove_from_blacklist_later(ip, duration))
        else:
            # Add to in-memory blacklist
            self.blacklist.add(ip)
    
    async def _remove_from_blacklist_later(self, ip: str, duration: int):
        """Remove IP from blacklist after duration."""
        await asyncio.sleep(duration)
        if self.redis:
            await self.redis.srem("ddos:blacklist", ip)
        else:
            self.blacklist.discard(ip)


class DDoSProtectionMiddleware:
    """FastAPI middleware for DDoS protection."""
    
    def __init__(self, app):
        self.app = app
        self.ddos_protection = DDoSProtection()
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            request = Request(scope, receive)
            
            # Skip protection for health endpoints
            if request.url.path in ["/health", "/metrics"]:
                await self.app(scope, receive, send)
                return
            
            # Check DDoS protection
            if response := await self.ddos_protection.check_request(request):
                await response(scope, receive, send)
                return
            
            await self.app(scope, receive, send)
        else:
            await self.app(scope, receive, send)