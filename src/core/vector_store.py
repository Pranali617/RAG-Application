from typing import List, Dict, Optional
from elasticsearch import Elasticsearch
import numpy as np
from sentence_transformers import SentenceTransformer
from src.core.elastic_client import get_es_client
from src.config import Config
import os

class ElasticsearchVectorStore:
    """Custom Elasticsearch vector store without LangChain"""
    
    def __init__(self):
        self.es = get_es_client()
        self.index_name = Config.ES_INDEX
        self.embedding_model = SentenceTransformer(Config.EMBEDDING_MODEL)
        self.embedding_dim = 384  # all-MiniLM-L6-v2 dimension
    
    def create_index_if_not_exists(self):
        """Create index with proper mapping"""
        if self.es.indices.exists(index=self.index_name):
            print(f"✓ Index '{self.index_name}' already exists")
            return
        
       # Inside create_index_if_not_exists method, update the mapping:

        mapping = {
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 0,
                "analysis": {
                    "analyzer": {
                        "default": {
                            "type": "standard"
                        }
                    }
                }
            },
            "mappings": {
                "properties": {
                    "page_content": {
                        "type": "text",
                        "analyzer": "standard"
                    },
                    "content_vector": {
                        "type": "dense_vector",
                        "dims": self.embedding_dim,
                        "index": True,
                        "similarity": "cosine"
                    },
                    "metadata": {
                        "properties": {
                            "source": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
                            "pdf_filename": {"type": "keyword"},  # NEW FIELD
                            "archive_name": {"type": "keyword"},  # NEW FIELD
                            "file_type": {"type": "keyword"},
                            "producer": {"type": "text"},
                            "creator": {"type": "text"},
                            "author": {"type": "text"},
                            "title": {"type": "text"},
                            "subject": {"type": "text"},
                            "keywords": {"type": "text"},
                            "creation_date": {"type": "date", "ignore_malformed": True},
                            "modification_date": {"type": "date", "ignore_malformed": True},
                            "total_pages": {"type": "integer"},
                            "page_number": {"type": "integer"},
                            "page_label": {"type": "keyword"},
                            "indexed_at": {"type": "date"}
                        }
                    },
                    "chunk_index": {"type": "integer"}
                }
            }
        }
            
        self.es.indices.create(index=self.index_name, body=mapping)
        print(f"✓ Created index '{self.index_name}'")
    
    def similarity_search(
        self, 
        query: str, 
        k: int = 5, 
        filter_dict: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Search for similar documents using hybrid search
        
        Args:
            query: Search query
            k: Number of results
            filter_dict: Metadata filters
        
        Returns:
            List of matching documents
        """
        # Generate query embedding
        query_vector = self.embedding_model.encode(query).tolist()
        
        # Build query
        must_clauses = []
        
        # Add filters if provided
        if filter_dict:
            for key, value in filter_dict.items():
                must_clauses.append({
                    "term": {f"metadata.{key}": value}
                })
        
        # Hybrid search: Vector + Text
        search_query = {
            "size": k,
            "query": {
                "bool": {
                    "must": must_clauses if must_clauses else [{"match_all": {}}],
                    "should": [
                        {
                            "script_score": {
                                "query": {"match_all": {}},
                                "script": {
                                    "source": "cosineSimilarity(params.query_vector, 'content_vector') + 1.0",
                                    "params": {"query_vector": query_vector}
                                }
                            }
                        },
                        {
                            "match": {
                                "page_content": {
                                    "query": query,
                                    "boost": 0.3
                                }
                            }
                        }
                    ],
                    "minimum_should_match": 1
                }
            }
        }
        
        try:
            response = self.es.search(index=self.index_name, body=search_query)
            return response['hits']['hits']
        except Exception as e:
            print(f"Search error: {e}")
            return []
    
    def add_documents(self, documents: List[Dict]) -> int:
        """
        Add documents to Elasticsearch
        
        Args:
            documents: List of dicts with 'page_content' and 'metadata'
        
        Returns:
            Number of documents indexed
        """
        from elasticsearch.helpers import bulk
        
        actions = []
        for i, doc in enumerate(documents):
            content = doc.get('page_content', '')
            metadata = doc.get('metadata', {})
            
            # Generate embedding
            vector = self.embedding_model.encode(content).tolist()
            
            action = {
                "_index": self.index_name,
                "_source": {
                    "page_content": content,
                    "content_vector": vector,
                    "metadata": metadata,
                    "chunk_index": i
                }
            }
            actions.append(action)
        
        # Bulk index
        success, failed = bulk(self.es, actions, raise_on_error=False)
        print(f"✓ Indexed {success} documents, {len(failed)} failed")
        
        return success
    
   
    
    def get_index_stats(self) -> Dict:
        """Get statistics about the index"""
        try:
            stats = self.es.indices.stats(index=self.index_name)
            doc_count = stats['indices'][self.index_name]['total']['docs']['count']
            size = stats['indices'][self.index_name]['total']['store']['size_in_bytes']
            
            return {
                "document_count": doc_count,
                "size_bytes": size,
                "size_mb": round(size / (1024 * 1024), 2)
            }
        except Exception as e:
            return {"error": str(e)}


# Singleton instance
vectorstore = ElasticsearchVectorStore()