import apiClient from "./client";

export const getCart = () => {
  return apiClient.get("/cart/cart");
};

export const addToCart = (productId, quantity) => {
  return apiClient.post("/cart/cart/items", { product_id: productId, quantity });
};

export const updateCartItem = (itemId, quantity) => {
  return apiClient.put(`/cart/cart/items/${itemId}`, { quantity });
};

export const removeCartItem = (itemId) => {
  return apiClient.delete(`/cart/cart/items/${itemId}`);
};

export const clearCart = () => {
  return apiClient.delete("/cart/cart");
};