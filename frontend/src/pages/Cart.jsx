import { useState } from "react";
import { Link } from "react-router-dom";
import { useCart } from "../context/CartContext";

function Cart() {
  const { cart, updateItem, removeItem } = useCart();
  const [error, setError] = useState("");

  if (!cart || cart.items.length === 0) {
    return (
      <div>
        <h2>Your Cart</h2>
        <p>Your cart is empty. <Link to="/products">Browse products</Link></p>
      </div>
    );
  }

  const handleQuantityChange = async (itemId, newQuantity) => {
    setError("");
    try {
      await updateItem(itemId, newQuantity);
    } catch (err) {
      setError(err.response?.data?.detail || "Could not update quantity.");
    }
  };

  return (
    <div>
      <h2>Your Cart</h2>
      {error && <p style={{ color: "red" }}>{error}</p>}

      {cart.items.map((item) => (
        <div key={item.id} style={{ display: "flex", gap: "1rem", alignItems: "center", padding: "0.5rem 0", borderBottom: "1px solid #333" }}>
          <span style={{ minWidth: "200px" }}>{item.product_name}</span>
          <span>₹{item.price_at_add} each</span>
          <input
            type="number"
            min="1"
            value={item.quantity}
            onChange={(e) => handleQuantityChange(item.id, parseInt(e.target.value) || 1)}
            style={{ width: "60px" }}
          />
          <span>₹{(item.price_at_add * item.quantity).toFixed(2)}</span>
          <button onClick={() => removeItem(item.id)}>Remove</button>
        </div>
      ))}

      <h3 style={{ marginTop: "1rem" }}>Total: ₹{cart.total}</h3>

      <Link to="/checkout">
        <button style={{ marginTop: "1rem" }}>Proceed to Checkout</button>
      </Link>
    </div>
  );
}

export default Cart;