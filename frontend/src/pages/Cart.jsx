import { useState } from "react";
import { Link } from "react-router-dom";
import { useCart } from "../context/CartContext";

function Cart() {
  const { cart, updateItem, removeItem } = useCart();
  const [error, setError] = useState("");

  if (!cart || cart.items.length === 0) {
    return (
      <div className="page page-medium">
        <h2>Your cart</h2>
        <div className="empty">
          <h3>Your cart is empty</h3>
          <p>Add something you like and it will show up here.</p>
          <Link to="/products" className="btn btn-primary">Browse products</Link>
        </div>
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

  const handleRemove = async (itemId) => {
    setError("");
    try {
      await removeItem(itemId);
    } catch (err) {
      setError(err.response?.data?.detail || "Could not remove the item.");
    }
  };

  return (
    <div className="page page-medium">
      <h2>Your cart</h2>
      {error && <div className="alert alert-error" role="alert">{error}</div>}

      <div className="panel">
        {cart.items.map((item) => (
          <div key={item.id} className="cart-row">
            <div>
              <div className="cart-name">{item.product_name}</div>
              <div className="muted">₹{item.price_at_add} each</div>
            </div>
            <input
              className="input input-qty"
              type="number"
              min="1"
              aria-label={`Quantity for ${item.product_name}`}
              value={item.quantity}
              onChange={(e) => handleQuantityChange(item.id, parseInt(e.target.value) || 1)}
            />
            <div className="cart-line-total">₹{(item.price_at_add * item.quantity).toFixed(2)}</div>
            <button className="btn btn-danger btn-sm" onClick={() => handleRemove(item.id)}>Remove</button>
          </div>
        ))}

        <div className="summary-total">
          <span>Total</span>
          <span>₹{cart.total}</span>
        </div>

        <div className="actions">
          <Link to="/products" className="btn btn-secondary">Keep shopping</Link>
          <Link to="/checkout" className="btn btn-primary">Proceed to checkout</Link>
        </div>
      </div>
    </div>
  );
}

export default Cart;
