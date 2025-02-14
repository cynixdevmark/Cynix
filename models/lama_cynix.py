from typing import Dict, Any, List, Optional
import torch
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    PreTrainedModel,
    PreTrainedTokenizer
)
import numpy as np
from torch.nn import functional as F


class LamaCynixModel:
    def __init__(
            self,
            model_path: str,
            device: str = "cuda" if torch.cuda.is_available() else "cpu"
    ):
        self.device = device
        self.tokenizer: PreTrainedTokenizer = AutoTokenizer.from_pretrained(
            model_path,
            trust_remote_code=True
        )
        self.model: PreTrainedModel = AutoModelForCausalLM.from_pretrained(
            model_path,
            trust_remote_code=True,
            torch_dtype=torch.float16 if device == "cuda" else torch.float32
        ).to(device)

        self.max_length = 2048
        self.temperature = 0.7
        self.top_p = 0.9

    def analyze_code_quality(self, repo_data: Dict[str, Any]) -> Dict[str, Any]:
        prompt = self._construct_code_analysis_prompt(repo_data)

        generated_text = self._generate_text(
            prompt,
            max_new_tokens=512,
            temperature=0.3  # Lower temperature for more focused analysis
        )

        return self._parse_code_analysis_response(generated_text)

    def analyze_meme_potential(
            self,
            image_features: Dict[str, Any],
            market_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        prompt = self._construct_meme_analysis_prompt(image_features, market_context)

        generated_text = self._generate_text(
            prompt,
            max_new_tokens=256,
            temperature=0.8  # Higher temperature for creative analysis
        )

        return self._parse_meme_analysis_response(generated_text)

    def analyze_influencer_credibility(
            self,
            twitter_data: Dict[str, Any],
            blockchain_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        prompt = self._construct_influencer_analysis_prompt(
            twitter_data,
            blockchain_data
        )

        generated_text = self._generate_text(
            prompt,
            max_new_tokens=384,
            temperature=0.5
        )

        return self._parse_influencer_analysis_response(generated_text)

    def _generate_text(
            self,
            prompt: str,
            max_new_tokens: int,
            temperature: float
    ) -> str:
        inputs = self.tokenizer(
            prompt,
            return_tensors="pt",
            truncation=True,
            max_length=self.max_length
        ).to(self.device)

        with torch.no_grad():
            output_sequences = self.model.generate(
                input_ids=inputs["input_ids"],
                attention_mask=inputs["attention_mask"],
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                top_p=self.top_p,
                do_sample=True,
                pad_token_id=self.tokenizer.pad_token_id,
                eos_token_id=self.tokenizer.eos_token_id
            )

        generated_text = self.tokenizer.decode(
            output_sequences[0],
            skip_special_tokens=True
        )
        return generated_text.replace(prompt, "").strip()

    def _construct_code_analysis_prompt(
            self,
            repo_data: Dict[str, Any]
    ) -> str:
        return f"""Analyze the following GitHub repository data for code quality and project potential:

Repository Information:
- Stars: {repo_data.get('stargazers_count', 0)}
- Forks: {repo_data.get('forks_count', 0)}
- Open Issues: {repo_data.get('open_issues_count', 0)}
- Last Updated: {repo_data.get('updated_at', 'unknown')}
- Language: {repo_data.get('language', 'unknown')}

Please evaluate the repository's:
1. Code maintenance and activity
2. Community engagement
3. Project maturity
4. Technical sophistication
5. Overall project potential

Analysis:"""

    def _parse_code_analysis_response(self, text: str) -> Dict[str, Any]:
        # Extract key metrics using simple heuristics
        lines = text.split('\n')
        scores = {}

        for line in lines:
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip().lower().replace(' ', '_')
                try:
                    # Try to extract numeric values
                    value = float([
                                      word for word in value.split()
                                      if word.replace('.', '').isdigit()
                                  ][0])
                    scores[key] = value
                except (IndexError, ValueError):
                    continue

        # Ensure all required metrics are present
        required_metrics = [
            'code_quality',
            'community_score',
            'maturity_score',
            'technical_score',
            'potential_score'
        ]

        for metric in required_metrics:
            if metric not in scores:
                scores[metric] = 0.0

        return scores

    def _construct_meme_analysis_prompt(
            self,
            image_features: Dict[str, Any],
            market_context: Optional[Dict[str, Any]] = None
    ) -> str:
        prompt = f"""Analyze the following meme image features for viral potential:

Image Features:
{self._format_dict(image_features)}

"""
        if market_context:
            prompt += f"""Market Context:
{self._format_dict(market_context)}

"""

        prompt += """Please evaluate the meme's:
1. Virality potential
2. Relevance to crypto community
3. Timing and trend alignment
4. Overall alpha signal strength

Analysis:"""
        return prompt

    def _format_dict(self, d: Dict[str, Any], indent: int = 0) -> str:
        result = []
        for k, v in d.items():
            if isinstance(v, dict):
                result.append(f"{'  ' * indent}- {k}:")
                result.append(self._format_dict(v, indent + 1))
            else:
                result.append(f"{'  ' * indent}- {k}: {v}")
        return "\n".join(result)