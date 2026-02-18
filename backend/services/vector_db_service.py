from qdrant_client import QdrantClient, models
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any
import uuid
import os

# Model_Path = "C:/coding/Major-Project-/backend/EM_Model/all-MiniLM-L6-v2"
Model_Path = "./EM_Model/all-MiniLM-L6-v2"
print(Model_Path)
class VectorDBService:
    """
    Manages interactions with the Qdrant vector database for storing and retrieving architecture patterns.
    """
    def __init__(self, collection_name="architecture_patterns"):
        # Initialize the Qdrant client to run in-memory for simplicity
        self.client = QdrantClient(":memory:")
        self.collection_name = collection_name
        
        # Load a pre-trained model for creating embeddings.
        print(f"INFO:     Loading embedding model from local path: {Model_Path}")
        self.embedding_model = SentenceTransformer(Model_Path)
        
        # Get the size of the vectors produced by the model
        self.vector_size = self.embedding_model.get_sentence_embedding_dimension()
        
        # Create the collection in Qdrant if it doesn't exist
        self.client.recreate_collection(
            collection_name=self.collection_name,
            vectors_config=models.VectorParams(size=self.vector_size, distance=models.Distance.COSINE),
        )
        print(f"✅ Vector DB Service initialized. Collection '{self.collection_name}' created.")

    def add_pattern(self, description: str, metadata: Dict[str, Any]):
        """
        Adds a new architecture pattern to the vector database.
        """
        vector = self.embedding_model.encode(description).tolist()
        
        self.client.upsert(
            collection_name=self.collection_name,
            points=[
                models.PointStruct(
                    id=str(uuid.uuid4()),
                    vector=vector,
                    payload={"description": description, "architecture": metadata}
                )
            ],
            wait=True
        )

    def search_similar_patterns(self, query: str, limit: int = 3) -> List[Dict[str, Any]]:
        """
        Searches for architecture patterns similar to the given query.
        """
        query_vector = self.embedding_model.encode(query).tolist()
        
        search_result = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            limit=limit
        )
        
        return [
            {
                "score": hit.score,
                "description": hit.payload.get("description"),
                "architecture": hit.payload.get("architecture")
            }
            for hit in search_result
        ]

# Global instance of the service
vector_db_service = VectorDBService()