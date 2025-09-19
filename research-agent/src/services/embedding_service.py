"""Embedding service for text vectorization using sentence-transformers"""

import asyncio
from typing import List, Optional, Union
import numpy as np
from sentence_transformers import SentenceTransformer
from structlog import get_logger
import torch

logger = get_logger()


class EmbeddingService:
    """Service for generating text embeddings using sentence-transformers"""

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        """
        Initialize the embedding service

        Args:
            model_name: Name of the sentence-transformer model to use
        """
        self.model_name = model_name
        self.model: Optional[SentenceTransformer] = None
        self.embedding_dim = 384  # Default for MiniLM-L6
        self._lock = asyncio.Lock()

    async def initialize(self):
        """Load the model asynchronously"""
        async with self._lock:
            if self.model is None:
                loop = asyncio.get_event_loop()
                self.model = await loop.run_in_executor(
                    None,
                    SentenceTransformer,
                    self.model_name
                )
                # Get actual embedding dimension
                self.embedding_dim = self.model.get_sentence_embedding_dimension()
                logger.info(
                    "Embedding model loaded",
                    model=self.model_name,
                    embedding_dim=self.embedding_dim
                )

    async def embed_text(self, text: Union[str, List[str]]) -> np.ndarray:
        """
        Generate embeddings for text

        Args:
            text: Single text string or list of texts

        Returns:
            Numpy array of embeddings
        """
        if self.model is None:
            await self.initialize()

        if isinstance(text, str):
            texts = [text]
        else:
            texts = text

        # Run encoding in executor to avoid blocking
        loop = asyncio.get_event_loop()
        embeddings = await loop.run_in_executor(
            None,
            self._encode_texts,
            texts
        )

        if isinstance(text, str):
            return embeddings[0]
        return embeddings

    def _encode_texts(self, texts: List[str]) -> np.ndarray:
        """Internal method to encode texts"""
        # Truncate long texts to avoid memory issues
        max_length = 512
        truncated_texts = [
            text[:max_length] if len(text) > max_length else text
            for text in texts
        ]

        # Generate embeddings
        with torch.no_grad():
            embeddings = self.model.encode(
                truncated_texts,
                convert_to_numpy=True,
                normalize_embeddings=True,  # Normalize for cosine similarity
                batch_size=32,
                show_progress_bar=False
            )

        return embeddings

    async def embed_batch(self, texts: List[str], batch_size: int = 32) -> List[np.ndarray]:
        """
        Generate embeddings for a batch of texts

        Args:
            texts: List of texts to embed
            batch_size: Batch size for processing

        Returns:
            List of embedding arrays
        """
        if not texts:
            return []

        all_embeddings = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            embeddings = await self.embed_text(batch)
            all_embeddings.extend(embeddings)

        return all_embeddings

    def compute_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Compute cosine similarity between two embeddings

        Args:
            embedding1: First embedding
            embedding2: Second embedding

        Returns:
            Cosine similarity score (0-1)
        """
        # Since embeddings are normalized, dot product gives cosine similarity
        return float(np.dot(embedding1, embedding2))

    def find_similar(
        self,
        query_embedding: np.ndarray,
        embeddings: List[np.ndarray],
        top_k: int = 5,
        threshold: float = 0.0
    ) -> List[tuple[int, float]]:
        """
        Find most similar embeddings to a query

        Args:
            query_embedding: Query embedding
            embeddings: List of embeddings to search
            top_k: Number of top results to return
            threshold: Minimum similarity threshold

        Returns:
            List of (index, similarity_score) tuples
        """
        if not embeddings:
            return []

        # Compute similarities
        similarities = [
            self.compute_similarity(query_embedding, emb)
            for emb in embeddings
        ]

        # Filter by threshold and sort
        results = [
            (idx, score)
            for idx, score in enumerate(similarities)
            if score >= threshold
        ]
        results.sort(key=lambda x: x[1], reverse=True)

        return results[:top_k]


# Global instance
_embedding_service: Optional[EmbeddingService] = None


async def get_embedding_service() -> EmbeddingService:
    """Get or create the global embedding service"""
    global _embedding_service

    if _embedding_service is None:
        _embedding_service = EmbeddingService()
        await _embedding_service.initialize()

    return _embedding_service