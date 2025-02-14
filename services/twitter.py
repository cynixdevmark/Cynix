from typing import Dict, Any, List, Optional
import tweepy
import asyncio
import json
from datetime import datetime
from models.lama_cynix import LamaCynixModel


class CynixTwitterBot:
    def __init__(
            self,
            config: Dict[str, Any],
            model: LamaCynixModel
    ):
        self.api = tweepy.Client(
            bearer_token=config["twitter_bearer_token"],
            consumer_key=config["consumer_key"],
            consumer_secret=config["consumer_secret"],
            access_token=config["access_token"],
            access_token_secret=config["access_token_secret"],
            wait_on_rate_limit=True
        )
        self.model = model
        self.config = config

    async def post_alpha_signal(
            self,
            signal_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Post an alpha signal as a thread"""
        try:
            # Generate tweet content
            tweet_content = self._generate_tweet_content(signal_data)
            thread_tweets = self._split_into_thread(tweet_content)

            # Post thread
            tweet_ids = []
            reply_to = None

            for tweet in thread_tweets:
                response = self.api.create_tweet(
                    text=tweet,
                    in_reply_to_tweet_id=reply_to
                )
                tweet_id = response.data["id"]
                tweet_ids.append(tweet_id)
                reply_to = tweet_id

                # Add small delay between tweets
                await asyncio.sleep(1)

            return {
                "success": True,
                "tweet_ids": tweet_ids,
                "thread_url": f"https://twitter.com/user/status/{tweet_ids[0]}"
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def post_meme_analysis(
            self,
            meme_data: Dict[str, Any],
            media_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """Post meme analysis with optional media"""
        try:
            # Generate analysis content
            analysis_content = self._generate_meme_analysis(meme_data)

            # Upload media if provided
            media_id = None
            if media_url:
                media_id = self._upload_media(media_url)

            # Post tweet
            response = self.api.create_tweet(
                text=analysis_content,
                media_ids=[media_id] if media_id else None
            )

            return {
                "success": True,
                "tweet_id": response.data["id"]
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def _generate_tweet_content(
            self,
            signal_data: Dict[str, Any]
    ) -> str:
        """Generate formatted tweet content from signal data"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M UTC")

        content = f"""🔥 CYNIX ALPHA ALERT 🔥

{signal_data['title']}

Signal Strength: {'🟢' * int(signal_data['confidence'] * 5)}
Confidence: {signal_data['confidence'] * 100:.1f}%

Key Insights:
{self._format_insights(signal_data['insights'])}

{timestamp}
#CynixAlpha #Solana"""

        return content

    def _format_insights(self, insights: List[str]) -> str:
        """Format insights into Twitter-friendly bullet points"""
        return "\n".join(f"• {insight}" for insight in insights)

    def _split_into_thread(
            self,
            content: str,
            max_length: int = 280
    ) -> List[str]:
        """Split content into thread-sized tweets"""
        words = content.split()
        tweets = []
        current_tweet = []
        current_length = 0

        for word in words:
            word_length = len(word) + 1  # +1 for space

            if current_length + word_length > max_length:
                tweets.append(" ".join(current_tweet))
                current_tweet = [word]
                current_length = word_length
            else:
                current_tweet.append(word)
                current_length += word_length

        if current_tweet:
            tweets.append(" ".join(current_tweet))

        return tweets

    def _generate_meme_analysis(
            self,
            meme_data: Dict[str, Any]
    ) -> str:
        """Generate meme analysis tweet content"""
        return f"""🎭 CYNIX MEME ANALYSIS 🎭

Virality Score: {meme_data['virality_score']}/100
Originality: {'✅' if meme_data['is_original'] else '⚠️'}

Trend Alignment: {meme_data['trend_alignment']}
Alpha Potential: {'🔥' * int(meme_data['alpha_potential'] / 20)}

#CynixMemes #SolanaMemes"""

    def _upload_media(self, media_url: str) -> Optional[str]:
        """Upload media to Twitter"""
        try:
            media = self.api.media_upload(media_url)
            return media.media_id
        except Exception as e:
            print(f"Error uploading media: {str(e)}")
            return None