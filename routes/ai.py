from fastapi import APIRouter, Header, HTTPException
from typing import Optional
from utils.test_data import get_test_data, update_test_data
from utils.premium import check_premium_status

router = APIRouter(prefix="/api", tags=["ai"])

# --- AI ---
@router.get("/ai/generate/facts/{card_id}/{card_type}")
async def ai_generate_facts(card_id: str, card_type: str, token: str = Header(None)):
    """Generate AI facts for a card"""
    if not check_premium_status(token):
        raise HTTPException(status_code=403, detail="Premium required")
    
    # Get AI facts from test data
    key = f"{card_id}_{card_type}"
    ai_facts = get_test_data("ai_facts", {})
    card_facts = ai_facts.get(key, {})
    
    if card_facts and "results" in card_facts:
        return {"facts": [fact["fact"] for fact in card_facts["results"]]}
    
    # Fallback to mock data if not found
    return {
        "facts": [
            f"AI generated fact 1 for {card_type} {card_id}",
            f"AI generated fact 2 for {card_type} {card_id}",
            f"AI generated fact 3 for {card_type} {card_id}"
        ]
    }

@router.get("/ai/generate/recommend/{card_id}/{card_type}")
async def ai_generate_recommendations(card_id: str, card_type: str, token: str = Header(None)):
    """Generate AI recommendations for a card"""
    if not check_premium_status(token):
        raise HTTPException(status_code=403, detail="Premium required")
    
    # Get AI recommendations from test data
    key = f"{card_id}_{card_type}"
    ai_recommend = get_test_data("ai_recommend", {})
    card_recommendations = ai_recommend.get(key, {})
    
    if card_recommendations and "results" in card_recommendations:
        return {"recommendations": card_recommendations["results"]}
    
    # Fallback to mock data if not found
    return {
        "recommendations": [
            {"id": "rec1", "title": f"Recommended {card_type} 1", "type": card_type},
            {"id": "rec2", "title": f"Recommended {card_type} 2", "type": card_type},
            {"id": "rec3", "title": f"Recommended {card_type} 3", "type": card_type}
        ]
    }

@router.get("/ai/search/{query}")
async def ai_search(query: str, token: str = Header(None)):
    """AI search functionality"""
    if not check_premium_status(token):
        raise HTTPException(status_code=403, detail="Premium required")
    
    # Get AI search results from test data
    ai_search_data = get_test_data("ai_search", {})
    search_results = ai_search_data.get(query, {})
    
    if search_results and "results" in search_results:
        return {"results": search_results["results"]}
    
    # Fallback to mock data if not found
    return {
        "results": [
            {"id": "ai1", "title": f"AI result for: {query}", "type": "movie"},
            {"id": "ai2", "title": f"AI result for: {query}", "type": "tv"},
            {"id": "ai3", "title": f"AI result for: {query}", "type": "anime"}
        ]
    } 