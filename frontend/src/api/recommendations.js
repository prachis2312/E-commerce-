import apiClient from "./client";

export const getSimilarProducts = (productId, topN = 5) => {
  return apiClient.get(`/recommendations/recommendations/similar/${productId}`, {
    params: { top_n: topN },
  });
};

export const getRecommendationsForUser = (userId, topN = 5) => {
  return apiClient.get(`/recommendations/recommendations/for-user/${userId}`, {
    params: { top_n: topN },
  });
};
// Admin only: re-embed new/changed products and drop deleted ones.
export const refreshRecommendations = () => {
  return apiClient.post("/recommendations/recommendations/refresh", null, { timeout: 120000 });
};
