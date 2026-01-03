"""
App Ratings API - Simple star rating system for user reviews
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import json
import os
from pathlib import Path

router = APIRouter(prefix="/api/ratings", tags=["ratings"])

# Simple file-based storage for ratings (can be migrated to DB later)
RATINGS_FILE = Path(__file__).parent.parent.parent / "data" / "ratings.json"

def ensure_data_dir():
    """Ensure data directory exists"""
    RATINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not RATINGS_FILE.exists():
        RATINGS_FILE.write_text(json.dumps({"ratings": [], "summary": {"total": 0, "average": 0, "count_by_stars": {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}}}))

def load_ratings():
    """Load ratings from file"""
    ensure_data_dir()
    try:
        return json.loads(RATINGS_FILE.read_text())
    except:
        return {"ratings": [], "summary": {"total": 0, "average": 0, "count_by_stars": {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}}}

def save_ratings(data):
    """Save ratings to file"""
    ensure_data_dir()
    RATINGS_FILE.write_text(json.dumps(data, indent=2, default=str))

# Request/Response Models
class RatingSubmission(BaseModel):
    stars: int = Field(..., ge=1, le=5, description="Rating from 1-5 stars")
    review: Optional[str] = Field(None, max_length=1000, description="Optional review text")
    user_name: Optional[str] = Field(None, max_length=100, description="Display name (optional)")

class RatingResponse(BaseModel):
    id: str
    stars: int
    review: Optional[str]
    user_name: str
    created_at: datetime

class RatingSummary(BaseModel):
    total_ratings: int
    average_rating: float
    count_by_stars: dict
    recent_reviews: List[RatingResponse]

class SubmitRatingResponse(BaseModel):
    success: bool
    message: str
    rating_id: str
    new_average: float

@router.post("/submit", response_model=SubmitRatingResponse)
async def submit_rating(submission: RatingSubmission):
    """Submit a new app rating"""
    try:
        data = load_ratings()

        # Generate unique ID
        rating_id = f"rating_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{len(data['ratings'])}"

        # Create rating entry
        rating = {
            "id": rating_id,
            "stars": submission.stars,
            "review": submission.review,
            "user_name": submission.user_name or "Anonymous User",
            "created_at": datetime.utcnow().isoformat()
        }

        # Add to ratings list
        data["ratings"].append(rating)

        # Update summary
        total = len(data["ratings"])
        stars_sum = sum(r["stars"] for r in data["ratings"])
        average = round(stars_sum / total, 1) if total > 0 else 0

        # Count by stars
        count_by_stars = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        for r in data["ratings"]:
            count_by_stars[r["stars"]] = count_by_stars.get(r["stars"], 0) + 1

        data["summary"] = {
            "total": total,
            "average": average,
            "count_by_stars": count_by_stars
        }

        save_ratings(data)

        return SubmitRatingResponse(
            success=True,
            message="Thank you for your rating!",
            rating_id=rating_id,
            new_average=average
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to submit rating: {str(e)}")

@router.get("/summary", response_model=RatingSummary)
async def get_rating_summary():
    """Get overall rating summary and recent reviews"""
    try:
        data = load_ratings()

        # Get recent reviews (last 10 with text)
        reviews_with_text = [r for r in data["ratings"] if r.get("review")]
        recent_reviews = sorted(reviews_with_text, key=lambda x: x["created_at"], reverse=True)[:10]

        return RatingSummary(
            total_ratings=data["summary"].get("total", 0),
            average_rating=data["summary"].get("average", 0),
            count_by_stars=data["summary"].get("count_by_stars", {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}),
            recent_reviews=[
                RatingResponse(
                    id=r["id"],
                    stars=r["stars"],
                    review=r.get("review"),
                    user_name=r.get("user_name", "Anonymous"),
                    created_at=datetime.fromisoformat(r["created_at"]) if isinstance(r["created_at"], str) else r["created_at"]
                )
                for r in recent_reviews
            ]
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get rating summary: {str(e)}")

@router.get("/all")
async def get_all_ratings(limit: int = 50, offset: int = 0):
    """Get all ratings with pagination"""
    try:
        data = load_ratings()

        # Sort by date descending
        sorted_ratings = sorted(data["ratings"], key=lambda x: x["created_at"], reverse=True)

        # Paginate
        paginated = sorted_ratings[offset:offset + limit]

        return {
            "ratings": paginated,
            "total": len(data["ratings"]),
            "limit": limit,
            "offset": offset
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get ratings: {str(e)}")
