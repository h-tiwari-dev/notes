import os
import json
import hashlib
import pickle
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import numpy as np


class ObsidianCache:
    """Cache system for Obsidian processor to avoid reprocessing the same files"""

    def __init__(self, cache_dir: str, vault_path: str):
        """
        Initialize the cache system

        :param cache_dir: Directory to store cache files
        :param vault_path: Path to the Obsidian vault (used for cache key generation)
        """
        self.cache_dir = Path(cache_dir)
        self.vault_path = vault_path
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Cache files
        self.embeddings_cache_file = self.cache_dir / "embeddings_cache.pkl"
        self.tags_cache_file = self.cache_dir / "tags_cache.pkl"
        self.similarities_cache_file = self.cache_dir / "similarities_cache.pkl"
        self.metadata_cache_file = self.cache_dir / "metadata_cache.json"

        # Initialize cache containers
        self.embeddings_cache = {}
        self.tags_cache = {}
        self.similarities_cache = {}
        self.file_metadata = {}

        # Load existing caches if available
        self._load_caches()

    def _load_caches(self):
        """Load all available caches from disk"""
        try:
            if self.embeddings_cache_file.exists():
                with open(self.embeddings_cache_file, "rb") as f:
                    self.embeddings_cache = pickle.load(f)

            if self.tags_cache_file.exists():
                with open(self.tags_cache_file, "rb") as f:
                    self.tags_cache = pickle.load(f)

            if self.similarities_cache_file.exists():
                with open(self.similarities_cache_file, "rb") as f:
                    self.similarities_cache = pickle.load(f)

            if self.metadata_cache_file.exists():
                with open(self.metadata_cache_file, "r", encoding="utf-8") as f:
                    self.file_metadata = json.load(f)
        except Exception as e:
            logging.warning(f"Error loading cache: {e}. Starting with fresh cache.")
            self.embeddings_cache = {}
            self.tags_cache = {}
            self.similarities_cache = {}
            self.file_metadata = {}

    def save_caches(self):
        """Save all caches to disk"""
        try:
            with open(self.embeddings_cache_file, "wb") as f:
                pickle.dump(self.embeddings_cache, f)

            with open(self.tags_cache_file, "wb") as f:
                pickle.dump(self.tags_cache, f)

            with open(self.similarities_cache_file, "wb") as f:
                pickle.dump(self.similarities_cache, f)

            with open(self.metadata_cache_file, "w", encoding="utf-8") as f:
                json.dump(self.file_metadata, f, indent=2)

            logging.info(f"Cache saved to {self.cache_dir}")
        except Exception as e:
            logging.error(f"Error saving cache: {e}")

    def get_file_hash(self, file_path: str, content: str) -> str:
        """
        Generate a hash for a file based on its content and modification time

        :param file_path: Path to the file
        :param content: File content
        :return: Hash string
        """
        # Use content hash and modification time for cache key
        content_hash = hashlib.md5(content.encode("utf-8")).hexdigest()
        mod_time = os.path.getmtime(file_path)
        return f"{content_hash}_{mod_time}"

    def is_file_changed(self, file_path: str, content: str) -> bool:
        """
        Check if a file has changed since last processing

        :param file_path: Path to the file
        :param content: File content
        :return: True if file has changed or not in cache
        """
        rel_path = os.path.relpath(file_path, self.vault_path)
        current_hash = self.get_file_hash(file_path, content)

        if rel_path not in self.file_metadata:
            return True

        return self.file_metadata[rel_path]["hash"] != current_hash

    def update_file_metadata(self, file_path: str, content: str):
        """
        Update file metadata in cache

        :param file_path: Path to the file
        :param content: File content
        """
        rel_path = os.path.relpath(file_path, self.vault_path)
        self.file_metadata[rel_path] = {
            "hash": self.get_file_hash(file_path, content),
            "last_processed": datetime.now().isoformat(),
        }

    def get_embedding(self, filename: str) -> Optional[np.ndarray]:
        """
        Get cached embedding for a file

        :param filename: Filename
        :return: Cached embedding or None
        """
        return self.embeddings_cache.get(filename)

    def set_embedding(self, filename: str, embedding: np.ndarray):
        """
        Cache embedding for a file

        :param filename: Filename
        :param embedding: Document embedding
        """
        self.embeddings_cache[filename] = embedding

    def get_tags(self, filename: str) -> Optional[List[str]]:
        """
        Get cached tags for a file

        :param filename: Filename
        :return: Cached tags or None
        """
        return self.tags_cache.get(filename)

    def set_tags(self, filename: str, tags: List[str]):
        """
        Cache tags for a file

        :param filename: Filename
        :param tags: Document tags
        """
        self.tags_cache[filename] = tags

    def get_similarities(self, filename: str) -> Optional[List[Dict[str, Any]]]:
        """
        Get cached similarities for a file

        :param filename: Filename
        :return: Cached similarities or None
        """
        return self.similarities_cache.get(filename)

    def set_similarities(self, filename: str, similarities: List[Dict[str, Any]]):
        """
        Cache similarities for a file

        :param filename: Filename
        :param similarities: Document similarities
        """
        self.similarities_cache[filename] = similarities

    def clear_cache(self):
        """Clear all caches"""
        self.embeddings_cache = {}
        self.tags_cache = {}
        self.similarities_cache = {}
        self.file_metadata = {}

        # Remove cache files
        if self.embeddings_cache_file.exists():
            self.embeddings_cache_file.unlink()
        if self.tags_cache_file.exists():
            self.tags_cache_file.unlink()
        if self.similarities_cache_file.exists():
            self.similarities_cache_file.unlink()
        if self.metadata_cache_file.exists():
            self.metadata_cache_file.unlink()

        logging.info("Cache cleared")
