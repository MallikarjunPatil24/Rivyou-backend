import difflib
from django.db.models import Q
from django.core.cache import cache
from .models import Product

def get_search_vocabulary():
    """
    Dynamically builds a vocabulary of search terms from categories, tags,
    and product names in the database, cached for 1 hour.
    """
    vocab = cache.get('search_vocabulary')
    if vocab is not None:
        return vocab
    
    vocab = set()
    try:
        # Fetch fields for all products to build vocabulary
        products = Product.objects.all().only('category', 'tags', 'product_name')
        for p in products:
            vocab.add(p.category.lower())
            # Handle plural/singular forms of categories
            if p.category.lower().endswith('s'):
                vocab.add(p.category.lower()[:-1])
            else:
                vocab.add(p.category.lower() + 's')
                
            if isinstance(p.tags, list):
                for t in p.tags:
                    vocab.add(str(t).lower())
            
            for word in p.product_name.lower().split():
                clean_word = ''.join(c for c in word if c.isalnum())
                if len(clean_word) > 2:
                    vocab.add(clean_word)
    except Exception:
        # Fallback if DB is not ready or has issues
        pass
        
    cache.set('search_vocabulary', vocab, 3600)
    return vocab

def correct_query(query):
    """
    Corrects spelling errors in query words using difflib sequence matching.
    """
    if not query:
        return query
    
    vocab = get_search_vocabulary()
    words = query.lower().split()
    corrected_words = []
    
    for word in words:
        clean_word = ''.join(c for c in word if c.isalnum())
        if not clean_word:
            continue
        
        # If exact match exists in vocabulary, keep it
        if clean_word in vocab:
            corrected_words.append(clean_word)
        else:
            # Find closest matching word in vocabulary
            matches = difflib.get_close_matches(clean_word, vocab, n=1, cutoff=0.75)
            if matches:
                corrected_words.append(matches[0])
            else:
                corrected_words.append(clean_word)
                
    return ' '.join(corrected_words) if corrected_words else query

def calculate_tag_score(tags, query):
    """
    Returns a float between 0 and 1.
    Exact match = 1.0, partial match = 0.5, no match = 0.0.
    If multiple tags match, average the scores.
    """
    if not tags or not query:
        return 0.0
    
    query_lower = query.lower()
    scores = []
    
    for tag in tags:
        tag_lower = str(tag).lower()
        if tag_lower == query_lower:
            scores.append(1.0)
        elif query_lower in tag_lower:
            scores.append(0.5)
            
    if not scores:
        return 0.0
        
    return sum(scores) / len(scores)

def search_products(query, limit=None, category_filter=None):
    """
    Search and rank products based on a query using a three-tier system:
    Tier 1: Category Match (Score: 0.8 - 1.0)
    Tier 2: Tag Match (Score: 0.4 - 0.79)
    Tier 3: Name/Description Match (Score: 0.1 - 0.39)
    
    Applies fuzzy logic to query spelling. Returns ALL matches, allowing view
    to slice results and report accurate total_results count.
    """
    if not query:
        return []
        
    # Apply spelling/typo correction
    corrected_q = correct_query(query)
    query_lower = corrected_q.lower()
    
    # 1. Fetch potential candidate products from database
    queryset = Product.objects.all()
    if category_filter:
        queryset = queryset.filter(category=category_filter)
        
    # Fetch candidates using a broad filtering query
    candidates = queryset.filter(
        Q(category__icontains=query_lower) |
        Q(product_name__icontains=query_lower) |
        Q(product_description__icontains=query_lower) |
        Q(tags__icontains=query_lower)
    )
    
    tier1_results = []
    tier2_results = []
    tier3_results = []
    
    for product in candidates:
        tags = product.tags if isinstance(product.tags, list) else []
        
        # --- TIER 1: Category match ---
        # Checks if query matches the category (e.g. "smartphone" in "Smartphones")
        if query_lower in product.category.lower() or product.category.lower() in query_lower:
            # Sub-sort: more matching tags = higher rank
            matching_tags_count = sum(1 for tag in tags if query_lower in str(tag).lower())
            relevance_score = round(0.80 + min(0.20, matching_tags_count * 0.05), 2)
            
            tier1_results.append({
                'id': product.id,
                'product_name': product.product_name,
                'category': product.category,
                'tags': tags,
                'relevance_score': relevance_score,
                'rank_reason': 'Category match'
            })
            continue
            
        # --- TIER 2: Tag match ---
        # Checks if any tag matches/contains the query (category does not match)
        exact_matches = [t for t in tags if str(t).lower() == query_lower]
        partial_matches = [t for t in tags if query_lower in str(t).lower() and str(t).lower() != query_lower]
        
        if exact_matches or partial_matches:
            if exact_matches:
                # Exact matches score between 0.60 and 0.79
                relevance_score = round(0.60 + min(0.19, len(exact_matches) * 0.05), 2)
                matched_tag = exact_matches[0]
            else:
                # Partial matches score between 0.40 and 0.59
                relevance_score = round(0.40 + min(0.19, len(partial_matches) * 0.05), 2)
                matched_tag = partial_matches[0]
                
            tier2_results.append({
                'id': product.id,
                'product_name': product.product_name,
                'category': product.category,
                'tags': tags,
                'relevance_score': relevance_score,
                'rank_reason': f"Tag match ({matched_tag})"
            })
            continue
            
        # --- TIER 3: Name/Description match ---
        in_name = query_lower in product.product_name.lower()
        in_desc = query_lower in product.product_description.lower()
        
        if in_name or in_desc:
            if in_name and in_desc:
                relevance_score = 0.35
            elif in_name:
                relevance_score = 0.25
            else:
                relevance_score = 0.15
                
            tier3_results.append({
                'id': product.id,
                'product_name': product.product_name,
                'category': product.category,
                'tags': tags,
                'relevance_score': relevance_score,
                'rank_reason': 'Name/Description match'
            })
            
    # Sort individual tiers by relevance_score descending
    tier1_results.sort(key=lambda x: x['relevance_score'], reverse=True)
    tier2_results.sort(key=lambda x: x['relevance_score'], reverse=True)
    tier3_results.sort(key=lambda x: x['relevance_score'], reverse=True)
    
    # Combine results
    combined_results = tier1_results + tier2_results + tier3_results
    
    # Apply limit in view, but if limit parameter is passed here we support it
    if limit is not None:
        return combined_results[:limit]
    return combined_results
