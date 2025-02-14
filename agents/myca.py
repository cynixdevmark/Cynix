from typing import Dict, Any
import io
import imagehash
from PIL import Image
import requests
from google.cloud import vision
from .base import BaseAgent
from models.lama_cynix import LamaCynixModel


class MycaAgent(BaseAgent):
    def __init__(self, model_path: str, config: Dict[str, Any]):
        super().__init__(model_path, config)
        self.model = LamaCynixModel(model_path)
        self.vision_client = vision.ImageAnnotatorClient()
        self.tineye_api_key = config["tineye_api_key"]

    async def _process_internal(self, data: Dict[str, Any]) -> Dict[str, Any]:
        image_data = await self._download_image(data["image_url"])
        image_hash = self._calculate_image_hash(image_data)

        originality_data = await self._check_image_originality(image_hash)
        vision_analysis = await self._analyze_image_content(image_data)
        alpha_potential = self._analyze_alpha_potential(vision_analysis)

        return {
            "is_original": originality_data["is_original"],
            "originality_score": originality_data["score"],
            "alpha_score": alpha_potential,
            "similar_images": originality_data["similar_images"],
            "content_analysis": vision_analysis
        }

    async def _download_image(self, url: str) -> bytes:
        async with self.session.get(url) as response:
            return await response.read()

    def _calculate_image_hash(self, image_data: bytes) -> str:
        image = Image.open(io.BytesIO(image_data))
        return str(imagehash.average_hash(image))

    async def _check_image_originality(self, image_hash: str) -> Dict[str, Any]:
        headers = {
            "X-Api-Key": self.tineye_api_key
        }

        response = requests.post(
            "https://api.tineye.com/rest/search/",
            files={"image": image_hash},
            headers=headers
        )

        search_results = response.json()
        similar_count = len(search_results.get("matches", []))

        return {
            "is_original": similar_count == 0,
            "score": 1.0 - (min(similar_count, 10) / 10),
            "similar_images": search_results.get("matches", [])[:5]
        }

    async def _analyze_image_content(self, image_data: bytes) -> Dict[str, Any]:
        image = vision.Image(content=image_data)

        response = self.vision_client.label_detection(image=image)
        labels = response.label_annotations

        response_safe = self.vision_client.safe_search_detection(image=image)
        safe_search = response_safe.safe_search_annotation

        return {
            "labels": [
                {"description": label.description, "score": label.score}
                for label in labels
            ],
            "safety_scores": {
                "adult": safe_search.adult,
                "violence": safe_search.violence,
                "spoof": safe_search.spoof
            }
        }

    def _analyze_alpha_potential(self, vision_analysis: Dict[str, Any]) -> float:
        meme_related_labels = ["meme", "funny", "humor", "viral", "trending"]

        relevance_score = sum(
            label["score"]
            for label in vision_analysis["labels"]
            if label["description"].lower() in meme_related_labels
        )

        safety_penalty = sum(
            getattr(vision_analysis["safety_scores"], key)
            for key in ["adult", "violence", "spoof"]
        ) / 15  # Normalize to 0-1

        return max(0, min(100, (relevance_score * 100) - (safety_penalty * 50)))