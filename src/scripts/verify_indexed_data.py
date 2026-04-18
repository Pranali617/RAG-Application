from src.core.vector_store import vectorstore
import json

def verify_indexed_documents():
    """Verify what's actually indexed in Elasticsearch"""
    
    print("\n" + "="*80)
    print("VERIFICATION: What's Indexed in Elasticsearch")
    print("="*80 + "\n")
    
    # Get all unique sources
    response = vectorstore.es.search(
        index=vectorstore.index_name,
        body={
            "size": 0,
            "aggs": {
                "sources": {
                    "terms": {
                        "field": "metadata.source.keyword",
                        "size": 1000
                    }
                },
                "file_types": {
                    "terms": {
                        "field": "metadata.file_type.keyword",
                        "size": 100
                    }
                }
            }
        }
    )
    
    print("📊 INDEX STATISTICS:")
    total_docs = vectorstore.get_index_stats()
    print(f"   Total indexed chunks: {total_docs.get('document_count', 0)}")
    print(f"   Index size: {total_docs.get('size_mb', 0)} MB\n")
    
    print("📁 INDEXED SOURCES:")
    sources = response['aggregations']['sources']['buckets']
    for bucket in sources:
        print(f"   ✓ {bucket['key']}: {bucket['doc_count']} chunks")
    
    print(f"\n📄 FILE TYPES:")
    file_types = response['aggregations']['file_types']['buckets']
    for bucket in file_types:
        print(f"   ✓ {bucket['key']}: {bucket['doc_count']} chunks")
    
    print("\n" + "="*80)
    
    # Check if we have PDF content or just ZIP content
    sample_docs = vectorstore.es.search(
        index=vectorstore.index_name,
        body={
            "size": 3,
            "query": {"match_all": {}}
        }
    )
    
    print("\n📝 SAMPLE DOCUMENTS:\n")
    for i, hit in enumerate(sample_docs['hits']['hits'], 1):
        source = hit['_source']
        metadata = source.get('metadata', {})
        content = source.get('page_content', '')
        
        print(f"Sample {i}:")
        print(f"   Source: {metadata.get('source', 'N/A')}")
        print(f"   File Type: {metadata.get('file_type', 'N/A')}")
        print(f"   Page Number: {metadata.get('page_number', 'N/A')}")
        print(f"   Total Pages: {metadata.get('total_pages', 'N/A')}")
        print(f"   Content Preview: {content[:150]}...")
        print()

if __name__ == "__main__":
    verify_indexed_documents()