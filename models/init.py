from .lama_cynix import LamaCynixModel

__version__ = "1.0.0"

def get_model(model_path: str, **kwargs):
    """Factory function to get appropriate model instance"""
    return LamaCynixModel(model_path, **kwargs)