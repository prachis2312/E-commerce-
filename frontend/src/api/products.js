import apiClient from "./client";

export const getProducts = ({ q, categoryId, minPrice, maxPrice, skip = 0, limit = 20 } = {}) => {
  return apiClient.get("/products/products", {
    params: {
      q: q || undefined,
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

// ---- Admin-only (backend enforces is_admin; the UI guard is just for convenience) ----

export const createProduct = (data) => apiClient.post("/products/products", data);

export const updateProduct = (productId, data) =>
  apiClient.put(`/products/products/${productId}`, data);

export const deleteProduct = (productId) =>
  apiClient.delete(`/products/products/${productId}`);

export const createCategory = (data) => apiClient.post("/products/categories", data);
