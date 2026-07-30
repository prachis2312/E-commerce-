import apiClient from "./client";

export const getProducts = ({ categoryId, minPrice, maxPrice, skip = 0, limit = 20 } = {}) => {
  return apiClient.get("/products/products", {
    params: {
      category_id: categoryId,
      min_price: minPrice,
      max_price: maxPrice,
      skip,
      limit,
    },
  });
};

export const getProduct = (productId) => {
  return apiClient.get(`/products/products/${productId}`);
};

export const getCategories = () => {
  return apiClient.get("/products/categories");
};