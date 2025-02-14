from typing import Dict, Any
import tweepy
from textblob import TextBlob
from collections import Counter
import numpy as np
from .base import BaseAgent
from blockchain.solana import SolanaClient
from models.lama_cynix import LamaCynixModel


class InfyAgent(BaseAgent):
    def __init__(self, model_path: str, config: Dict[str, Any]):
        super().__init__(model_path, config)
        self.model = LamaCynixModel(model_path)
        self.twitter_client = tweepy.Client(
            bearer_token=config["twitter_bearer_token"],
            wait_on_rate_limit=True
        )
        self.solana_client = SolanaClient(config["solana_rpc_url"])

    async def _process_internal(self, data: Dict[str, Any]) -> Dict[str, Any]:
        twitter_history = self._fetch_twitter_history(data["twitter_handle"])
        writing_style = self._analyze_writing_style(twitter_history)
        ca_verification = await self._verify_ca_history(
            twitter_history,
            data.get("known_addresses", [])
        )

        trust_score = self._calculate_trust_score(
            twitter_history,
            writing_style,
            ca_verification
        )

        return {
            "trust_score": trust_score,
            "writing_style_analysis": writing_style,
            "ca_verification": ca_verification,
            "engagement_metrics": self._calculate_engagement_metrics(twitter_history)
        }

    def _fetch_twitter_history(self, handle: str) -> Dict[str, Any]:
        user = self.twitter_client.get_user(
            username=handle,
            user_fields=['public_metrics', 'created_at']
        )

        tweets = self.twitter_client.get_users_tweets(
            user.data.id,
            max_results=100,
            tweet_fields=['public_metrics', 'created_at'],
            exclude=['retweets', 'replies']
        )

        return {
            "user_data": user.data,
            "tweets": tweets.data
        }

    def _analyze_writing_style(self, twitter_history: Dict[str, Any]) -> Dict[str, Any]:
        tweets = [tweet.text for tweet in twitter_history["tweets"]]

        # Analyze sentiment and subjectivity
        sentiments = [TextBlob(tweet).sentiment for tweet in tweets]

        # Analyze common phrases and vocabulary
        word_freq = Counter(" ".join(tweets).split())

        # Calculate style consistency
        style_metrics = {
            "avg_tweet_length": np.mean([len(tweet) for tweet in tweets]),
            "vocab_diversity": len(word_freq) / sum(word_freq.values()),
            "sentiment_consistency": np.std([s.polarity for s in sentiments]),
            "common_phrases": self._extract_common_phrases(tweets)
        }

        return style_metrics

    async def _verify_ca_history(
            self,
            twitter_history: Dict[str, Any],
            known_addresses: list
    ) -> Dict[str, Any]:
        ca_mentions = self._extract_solana_addresses(twitter_history)

        verification_results = []
        for address in ca_mentions:
            history = await self.solana_client.get_account_history(address)
            verification_results.append({
                "address": address,
                "transaction_count": history["transaction_count"],
                "is_contract": history["is_contract"],
                "first_seen": history["first_seen"],
                "is_known": address in known_addresses
            })

        return {
            "verified_addresses": verification_results,
            "known_address_match_rate": len(
                [r for r in verification_results if r["is_known"]]
            ) / len(verification_results) if verification_results else 0
        }

    def _calculate_trust_score(
            self,
            twitter_history: Dict[str, Any],
            writing_style: Dict[str, Any],
            ca_verification: Dict[str, Any]
    ) -> float:
        account_age_score = self._calculate_account_age_score(
            twitter_history["user_data"].created_at
        )
        engagement_score = self._calculate_engagement_score(twitter_history)
        style_consistency_score = 1 - writing_style["sentiment_consistency"]
        ca_verification_score = ca_verification["known_address_match_rate"]

        weights = {
            "account_age": 0.2,
            "engagement": 0.3,
            "style_consistency": 0.25,
            "ca_verification": 0.25
        }

        return sum([
            account_age_score * weights["account_age"],
            engagement_score * weights["engagement"],
            style_consistency_score * weights["style_consistency"],
            ca_verification_score * weights["ca_verification"]
        ]) * 100