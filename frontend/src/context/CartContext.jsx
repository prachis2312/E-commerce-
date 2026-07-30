import { createContext, useContext, useState, useEffect } from "react";
import { getCart, addToCart, updateCartItem, removeCartItem, clearCart } from "../api/cart";
import { useAuth } from "./AuthContext";

const CartContext = createContext(null);

export function CartProvider({ children }) {
  const [cart, setCart] = useState(null);
  const { isAuthenticated } = useAuth();

  // Load the cart whenever someone logs in; clear it locally on logout
  // (their actual cart still exists on the backend, we just stop showing it
  // client-side since /cart requires auth and would 401 otherwise).
  useEffect(() => {
    if (isAuthenticated) {
      getCart()
        .then((res) => setCart(res.data))
        .catch(() => setCart(null));
    } else {
      setCart(null);
    }
  }, [isAuthenticated]);

  const addItem = async (productId, quantity) => {
    const res = await addToCart(productId, quantity);
    setCart(res.data);
  };

  const updateItem = async (itemId, quantity) => {
    const res = await updateCartItem(itemId, quantity);
    setCart(res.data);
  };

  const removeItem = async (itemId) => {
    const res = await removeCartItem(itemId);
    setCart(res.data);
  };

  const clear = async () => {
    await clearCart();
    setCart(null);
  };

  const refreshCart = async () => {
  try {
    const res = await getCart();
    setCart(res.data);
  } catch {
    setCart(null);
  }
};

  const itemCount = cart ? cart.items.reduce((sum, item) => sum + item.quantity, 0) : 0;

  const value = { cart, itemCount, addItem, updateItem, removeItem, clear, refreshCart };

  return <CartContext.Provider value={value}>{children}</CartContext.Provider>;
}

export function useCart() {
  return useContext(CartContext);
}