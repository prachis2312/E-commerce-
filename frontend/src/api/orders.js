import apiClient from "./client";

export const checkout = (paymentMethod = "card") => {
  return apiClient.post("/orders/orders", { payment_method: paymentMethod });
};

export const buyNow = (productId, quantity = 1, paymentMethod = "card") => {
  return apiClient.post("/orders/orders/buy-now", {
    product_id: productId,
    quantity,
    payment_method: paymentMethod,
  });
};

export const getOrders = () => {
  return apiClient.get("/orders/orders");
};

export const getOrder = (orderId) => {
  return apiClient.get(`/orders/orders/${orderId}`);
};