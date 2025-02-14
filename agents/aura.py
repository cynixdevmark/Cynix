from typing import Dict, Any
import aiohttp
from .base import BaseAgent
from models.lama_cynix import LamaCynixModel
from blockchain.solana import SolanaClient
import tweepy


class AuraAgent(BaseAgent):
    def __init__(self, model_path: str, config: Dict[str, Any]):
        super().__init__(model_path, config)
        self.model = LamaCynixModel(model_path)
        self.github_token = config["github_token"]
        self.twitter_client = tweepy.Client(
            bearer_token=config["twitter_bearer_token"],
            wait_on_rate_limit=True
        )
        self.solana_client = SolanaClient(config["solana_rpc_url"])

    async def _process_internal(self, data: Dict[str, Any]) -> Dict[str, Any]:
        github_data = await self._fetch_github_data(data["github_url"])
        twitter_data = self._fetch_twitter_data(data["twitter_handle"])

        code_analysis = self._analyze_codebase(github_data)
        ca_history = await self.solana_client.get_account_history(
            data["contract_address"]
        )
        alpha_score = self._calculate_alpha_score(twitter_data)

        return {
            "project_value_score": self._calculate_project_score(
                code_analysis,
                ca_history,
                alpha_score
            ),
            "code_quality": code_analysis,
            "ca_reliability": ca_history,
            "alpha_potential": alpha_score
        }

    async def _fetch_github_data(self, github_url: str) -> Dict[str, Any]:
        repo_path = github_url.replace("https://github.com/", "")
        async with self.session.get(
                f"https://api.github.com/repos/{repo_path}",
                headers={
                    "Authorization": f"token {self.github_token}",
                    "Accept": "application/vnd.github.v3+json"
                }
        ) as response:
            return await response.json()

    def _fetch_twitter_data(self, handle: str) -> Dict[str, Any]:
        user = self.twitter_client.get_user(
            username=handle,
            user_fields=['public_metrics', 'created_at']
        )
        tweets = self.twitter_client.get_users_tweets(
            user.data.id,
            max_results=100,
            tweet_fields=['public_metrics', 'created_at']
        )
        return {
            "user_data": user.data,
            "tweets": tweets.data
        }

    def _analyze_codebase(self, github_data: Dict[str, Any]) -> Dict[str, Any]:
        commit_frequency = github_data.get('commit_count', 0) / 30  # last 30 days
        issues_count = github_data.get('open_issues_count', 0)
        stars_count = github_data.get('stargazers_count', 0)

        return {
            "commit_activity_score": min(commit_frequency / 10, 1.0),
            "community_engagement": min(issues_count / 100, 1.0),
            "popularity": min(stars_count / 1000, 1.0)
        }

    def _calculate_alpha_score(self, twitter_data: Dict[str, Any]) -> float:
        user_metrics = twitter_data['user_data'].public_metrics
        engagement_rate = (
                                  user_metrics['like_count'] + user_metrics['retweet_count']
                          ) / user_metrics['followers_count']

        return min(engagement_rate * 100, 100)  # Scale to 0-100