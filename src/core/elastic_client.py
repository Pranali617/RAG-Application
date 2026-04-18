from elasticsearch import Elasticsearch, ConnectionError
import requests
import time
import os
from dotenv import load_dotenv

load_dotenv()

def get_es_client():
    """
    Get Elasticsearch client for Elasticsearch 8.x
    """
    es_url = os.getenv("ES_URL", "http://localhost:9200")
    
    print(f"Attempting to connect to Elasticsearch at: {es_url}")
    
    # First, test basic HTTP connection
    try:
        response = requests.get(es_url, timeout=10)
        if response.status_code == 200:
            print(f"✓ Elasticsearch HTTP endpoint is responding")
            data = response.json()
            print(f"  Version: {data['version']['number']}")
            print(f"  Cluster: {data['cluster_name']}")
        else:
            print(f"✗ Elasticsearch returned status {response.status_code}")
            return None
    except requests.ConnectionError as e:
        print(f"✗ Cannot connect to Elasticsearch at {es_url}")
        print(f"Error: {e}")
        return None
    
    # Create Elasticsearch client with proper configuration for ES 8.x
    try:
        # For Elasticsearch 8.x with security disabled
        es = Elasticsearch(
            es_url,
            request_timeout=30,
            max_retries=3,
            retry_on_timeout=True,
            verify_certs=False,  # Disable SSL verification for local development
            ssl_show_warn=False
        )
        
        # Try a simple operation instead of ping
        try:
            info = es.info()
            print(f"✓ Elasticsearch client connected successfully")
            print(f"  Cluster name: {info['cluster_name']}")
            print(f"  Node name: {info['name']}")
            return es
        except Exception as e:
            print(f"✗ Elasticsearch client operation failed: {e}")
            print("Trying alternative connection method...")
            
            # Try with basic auth (even if disabled, some versions need it)
            es = Elasticsearch(
                es_url,
                basic_auth=('elastic', '') if ':9200' in es_url else None,
                request_timeout=30,
                verify_certs=False,
                ssl_show_warn=False
            )
            
            info = es.info()
            print(f"✓ Connected with alternative method")
            return es
            
    except Exception as e:
        print(f"✗ Error creating Elasticsearch client: {e}")
        return None

def create_index():
    """
    Create index if it doesn't exist
    """
    es = get_es_client()
    if es is None:
        print("✗ Cannot create index - Elasticsearch client is None")
        return False
    
    index_name = os.getenv("ES_INDEX", "pdf_search_index")
    
    try:
        # Check if index exists using a simpler approach
        try:
            exists = es.indices.exists(index=index_name)
            if exists:
                print(f"✓ Index '{index_name}' already exists")
                
                # Show index info
                stats = es.indices.stats(index=index_name)
                doc_count = stats['indices'][index_name]['total']['docs']['count']
                print(f"  Documents in index: {doc_count}")
                return True
        except Exception as e:
            print(f"⚠ Error checking index existence: {e}")
        
        # Create index with mapping
        print(f"Creating index '{index_name}'...")
        mapping = {
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 0
            },
            "mappings": {
                "properties": {
                    "page_content": {
                        "type": "text",
                        "analyzer": "english"
                    },
                    "content_vector": {
                        "type": "dense_vector",
                        "dims": 384,
                        "index": True,
                        "similarity": "cosine"
                    },
                    "metadata": {
                        "type": "object",
                        "properties": {
                            "source": {"type": "keyword"},
                            "owner": {"type": "keyword"},
                            "file_type": {"type": "keyword"}
                        }
                    }
                }
            }
        }
        
        es.indices.create(index=index_name, body=mapping)
        print(f"✓ Index '{index_name}' created successfully")
        return True
        
    except Exception as e:
        print(f"✗ Error creating index: {e}")
        
        # Try simpler mapping
        print("Trying simpler mapping...")
        try:
            simple_mapping = {
                "mappings": {
                    "properties": {
                        "page_content": {"type": "text"},
                        "content_vector": {
                            "type": "dense_vector",
                            "dims": 384
                        }
                    }
                }
            }
            es.indices.create(index=index_name, body=simple_mapping)
            print(f"✓ Index '{index_name}' created with simple mapping")
            return True
        except Exception as e2:
            print(f"✗ Failed with simple mapping too: {e2}")
            return False