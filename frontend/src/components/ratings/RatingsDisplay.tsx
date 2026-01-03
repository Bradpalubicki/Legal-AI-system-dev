'use client';

import React, { useEffect, useState } from 'react';
import { Star, MessageSquare, User } from 'lucide-react';
import { StarRating } from './StarRating';
import { API_CONFIG } from '@/config/api';

interface Review {
  id: string;
  stars: number;
  review: string | null;
  user_name: string;
  created_at: string;
}

interface RatingSummary {
  total_ratings: number;
  average_rating: number;
  count_by_stars: Record<number, number>;
  recent_reviews: Review[];
}

interface RatingsDisplayProps {
  compact?: boolean;
  showReviews?: boolean;
  maxReviews?: number;
}

export function RatingsDisplay({
  compact = false,
  showReviews = true,
  maxReviews = 3
}: RatingsDisplayProps) {
  const [summary, setSummary] = useState<RatingSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    const fetchRatings = async () => {
      try {
        const response = await fetch(`${API_CONFIG.BASE_URL}/api/ratings/summary`);
        if (response.ok) {
          const data = await response.json();
          setSummary(data);
        } else {
          setError(true);
        }
      } catch (err) {
        console.error('Failed to fetch ratings:', err);
        setError(true);
      } finally {
        setLoading(false);
      }
    };

    fetchRatings();
  }, []);

  if (loading) {
    return (
      <div className="animate-pulse">
        <div className="h-8 bg-gray-200 rounded w-32 mb-2"></div>
        <div className="h-4 bg-gray-200 rounded w-24"></div>
      </div>
    );
  }

  if (error || !summary || summary.total_ratings === 0) {
    // Don't show anything if there are no ratings yet
    return null;
  }

  if (compact) {
    return (
      <div className="flex items-center gap-2">
        <StarRating rating={summary.average_rating} readonly size="sm" />
        <span className="text-sm text-gray-600">
          {summary.average_rating.toFixed(1)} ({summary.total_ratings} reviews)
        </span>
      </div>
    );
  }

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    });
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
      {/* Summary Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-xl font-bold text-navy-800 mb-1">User Reviews</h3>
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2">
              <span className="text-3xl font-bold text-navy-800">
                {summary.average_rating.toFixed(1)}
              </span>
              <StarRating rating={summary.average_rating} readonly size="md" />
            </div>
            <span className="text-gray-500">
              ({summary.total_ratings} {summary.total_ratings === 1 ? 'review' : 'reviews'})
            </span>
          </div>
        </div>
      </div>

      {/* Rating Distribution */}
      <div className="mb-6 space-y-2">
        {[5, 4, 3, 2, 1].map((stars) => {
          const count = summary.count_by_stars[stars] || 0;
          const percentage = summary.total_ratings > 0
            ? (count / summary.total_ratings) * 100
            : 0;

          return (
            <div key={stars} className="flex items-center gap-2 text-sm">
              <span className="w-8 text-gray-600">{stars}</span>
              <Star className="w-4 h-4 fill-yellow-400 text-yellow-400" />
              <div className="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden">
                <div
                  className="h-full bg-yellow-400 rounded-full transition-all duration-500"
                  style={{ width: `${percentage}%` }}
                />
              </div>
              <span className="w-12 text-gray-500 text-right">{count}</span>
            </div>
          );
        })}
      </div>

      {/* Recent Reviews */}
      {showReviews && summary.recent_reviews.length > 0 && (
        <div className="border-t border-gray-100 pt-6">
          <h4 className="text-sm font-semibold text-gray-700 mb-4 flex items-center gap-2">
            <MessageSquare className="w-4 h-4" />
            Recent Reviews
          </h4>
          <div className="space-y-4">
            {summary.recent_reviews.slice(0, maxReviews).map((review) => (
              <div
                key={review.id}
                className="bg-gray-50 rounded-lg p-4"
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <div className="w-8 h-8 bg-navy-100 rounded-full flex items-center justify-center">
                      <User className="w-4 h-4 text-navy-600" />
                    </div>
                    <span className="font-medium text-gray-900">
                      {review.user_name}
                    </span>
                  </div>
                  <StarRating rating={review.stars} readonly size="sm" />
                </div>
                {review.review && (
                  <p className="text-gray-600 text-sm leading-relaxed">
                    "{review.review}"
                  </p>
                )}
                <p className="text-xs text-gray-400 mt-2">
                  {formatDate(review.created_at)}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default RatingsDisplay;
