from typing import Dict, Any, Optional, List
import asyncio
import aioredis
import json
from datetime import datetime, timedelta
from blockchain.token import CynixToken


class DataAccessService:
    def __init__(
            self,
            config: Dict[str, Any],
            cynix_token: CynixToken
    ):
        self.config = config
        self.cynix_token = cynix_token
        self.redis = aioredis.from_url(
            config["redis_url"],
            encoding="utf-8",
            decode_responses=True
        )
        self.cache_ttl = 300  # 5 minutes

    async def get_raw_data(
            self,
            wallet_address: str,
            data_type: str,
            params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Get raw data for analysis"""
        try:
            # Verify access level
            access_info = await self.cynix_token.check_access_level(wallet_address)
            if not access_info["access_levels"]["raw_data_access"]:
                return {
                    "error": "Insufficient token stake for raw data access"
                }

            # Check cache first
            cache_key = self._generate_cache_key(data_type, params)
            cached_data = await self.redis.get(cache_key)

            if cached_data:
                return json.loads(cached_data)

            # Fetch fresh data
            data = await self._fetch_raw_data(data_type, params)

            # Cache the result
            await self.redis.setex(
                cache_key,
                self.cache_ttl,
                json.dumps(data)
            )

            # Log access
            await self._log_data_access(
                wallet_address,
                data_type,
                params
            )

            return data

        except Exception as e:
            return {"error": str(e)}

    async def get_analytics_data(
            self,
            wallet_address: str,
            metric: str,
            timeframe: str = "24h"
    ) -> Dict[str, Any]:
        """Get aggregated analytics data"""
        try:
            # Get time range
            time_ranges = {
                "24h": timedelta(days=1),
                "7d": timedelta(days=7),
                "30d": timedelta(days=30)
            }

            if timeframe not in time_ranges:
                return {"error": "Invalid timeframe"}

            # Fetch and aggregate data
            end_time = datetime.utcnow()
            start_time = end_time - time_ranges[timeframe]

            aggregated_data = await self._aggregate_metric(
                metric,
                start_time,
                end_time
            )

            return {
                "metric": metric,
                "timeframe": timeframe,
                "data": aggregated_data
            }

        except Exception as e:
            return {"error": str(e)}

    async def _fetch_raw_data(
            self,
            data_type: str,
            params: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Fetch raw data from various sources"""
        data_fetchers = {
            "github": self._fetch_github_data,
            "twitter": self._fetch_twitter_data,
            "blockchain": self._fetch_blockchain_data
        }

        if data_type not in data_fetchers:
            raise ValueError(f"Unsupported data type: {data_type}")

        return await data_fetchers[data_type](params or {})

    async def _aggregate_metric(
            self,
            metric: str,
            start_time: datetime,
            end_time: datetime
    ) -> List[Dict[str, Any]]:
        """Aggregate metric data for the given timeframe"""
        # Get raw data points
        data_points = await self._get_metric_data_points(
            metric,
            start_time,
            end_time
        )

        # Aggregate by appropriate interval
        time_diff = end_time - start_time
        if time_diff <= timedelta(days=1):
            interval = timedelta(hours=1)
        elif time_diff <= timedelta(days=7):
            interval = timedelta(days=1)
        else:
            interval = timedelta(days=7)

        return self._aggregate_by_interval(
            data_points,
            start_time,
            end_time,
            interval
        )

    def _generate_cache_key(
            self,
            data_type: str,
            params: Optional[Dict[str, Any]]
    ) -> str:
        """Generate Redis cache key"""
        if params:
            param_str = json.dumps(
                params,
                sort_keys=True
            )
            return f"cynix:raw:{data_type}:{param_str}"
        return f"cynix:raw:{data_type}"

    async def _log_data_access(
            self,
            wallet_address: str,
            data_type: str,
            params: Optional[Dict[str, Any]]
    ):
        """Log data access for analytics"""
        log_entry = {
            "wallet_address": wallet_address,
            "data_type": data_type,
            "params": params,
            "timestamp": datetime.utcnow().isoformat()
        }

        await self.redis.lpush(
            "cynix:access_logs",
            json.dumps(log_entry)
        )
        await self.redis.ltrim("cynix:access_logs", 0, 9999)  # Keep last 10K logs