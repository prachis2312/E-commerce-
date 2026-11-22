import { useState } from "react";
import { useNavigate, useLocation, Link } from "react-router-dom";
import { checkout, buyNow } from "../api/orders";
import { useCart } from "../context/CartContext";

function Checkout() {
  const { cart, refreshCart } = useCart();
  const location = useLocation();
  const buyNowItem = location.state?.buyNowProduct; // { product, quantity } or undefined

  const [paymentMethod, setPaymentMethod] = useState("card");
  const [error, setError] = useState("");
  const [processing, setProcessing] = useState(false);
  const navigate = useNavigate();

  const isBuyNow = !!buyNowItem;

  // Only block on an empty cart if we're in cart-checkout mode —
  // Buy Now mode has its own product regardless of cart state.
  if (!isBuyNow && (!cart || cart.items.length === 0)) {
    return (
      <div className="page page-medium">
        <h2>Checkout</h2>
        <div className="empty">
          <h3>Your cart is empty</h3>
          <p>There is nothing to check out yet.</p>
          <Link to="/products" className="btn btn-primary">Browse products</Link>
        </div>
      </div>
    );
  }

  const handlePlaceOrder = async () => {
    setError("");
    setProcessing(true);
    try {
      let res;
      if (isBuyNow) {
        res = await buyNow(buyNowItem.product.id, buyNowItem.quantity, paymentMethod);
      } else {
        res = await checkout(paymentMethod);
        await refreshCart(); // sync local cart state now that the server has cleared it
      }
      navigate("/orders", { state: { justPlaced: res.data } });
    } catch (err) {
      if (err.response && err.response.status === 402) {
        setError(err.response.data.detail || "Payment was declined. Please try again.");
      } else if (err.response && err.response.data && err.response.data.detail) {
        setError(err.response.data.detail);
      } else {
        setError("Checkout failed. Please try again.");
      }
    } finally {
      setProcessing(false);
    }
  };

  const lines = isBuyNow
    ? [{ id: "buy-now", name: buyNowItem.product.name, quantity: buyNowItem.quantity, total: buyNowItem.product.price * buyNowItem.quantity }]
    : cart.items.map((item) => ({ id: item.id, name: item.product_name, quantity: item.quantity, total: item.price_at_add * item.quantity }));
  const grandTotal = isBuyNow ? (buyNowItem.product.price * buyNowItem.quantity).toFixed(2) : cart.total;

  return (
    <div className="page page-medium">
      <h2>Checkout</h2>

      <div className="panel">
        <h3>Order summary</h3>
        {lines.map((line) => (
          <div key={line.id} className="summary-line">
            <span>{line.name} × {line.quantity}</span>
            <span>₹{line.total.toFixed(2)}</span>
          </div>
        ))}
        <div className="summary-total">
          <span>Total</span>
          <span>₹{grandTotal}</span>
        </div>
      </div>

      <div className="panel" style={{ marginTop: "1.25rem" }}>
        <div className="field" style={{ marginBottom: 0 }}>
          <label htmlFor="payment">Payment method</label>
          <select id="payment" className="select" value={paymentMethod} onChange={(e) => setPaymentMethod(e.target.value)}>
            <option value="card">Card</option>
            <option value="upi">UPI</option>
            <option value="cod">Cash on delivery</option>
          </select>
        </div>
      </div>

      {error && <div className="alert alert-error" role="alert" style={{ marginTop: "1.25rem" }}>{error}</div>}

      <div className="actions">
        <Link to={isBuyNow ? "/products" : "/cart"} className="btn btn-secondary">Back</Link>
        <button className="btn btn-primary" onClick={handlePlaceOrder} disabled={processing}>
          {processing ? "Processing payment..." : "Place order"}
        </button>
      </div>
    </div>
  );
}

export default Checkout;
