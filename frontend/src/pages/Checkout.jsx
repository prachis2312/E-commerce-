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
      <div>
        <h2>Checkout</h2>
        <p>Your cart is empty. <Link to="/products">Browse products</Link></p>
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

  return (
    <div>
      <h2>Checkout</h2>

      <h3>Order Summary</h3>
      {isBuyNow ? (
        <div>
          {buyNowItem.product.name} × {buyNowItem.quantity} — ₹
          {(buyNowItem.product.price * buyNowItem.quantity).toFixed(2)}
        </div>
      ) : (
        cart.items.map((item) => (
          <div key={item.id}>
            {item.product_name} × {item.quantity} — ₹{(item.price_at_add * item.quantity).toFixed(2)}
          </div>
        ))
      )}

      <h3>
        Total: ₹
        {isBuyNow
          ? (buyNowItem.product.price * buyNowItem.quantity).toFixed(2)
          : cart.total}
      </h3>

      <div style={{ marginTop: "1rem" }}>
        <label>
          Payment Method:{" "}
          <select value={paymentMethod} onChange={(e) => setPaymentMethod(e.target.value)}>
            <option value="card">Card</option>
            <option value="upi">UPI</option>
            <option value="cod">Cash on Delivery</option>
          </select>
        </label>
      </div>

      {error && <p style={{ color: "red" }}>{error}</p>}

      <button onClick={handlePlaceOrder} disabled={processing} style={{ marginTop: "1rem" }}>
        {processing ? "Processing payment..." : "Place Order"}
      </button>
    </div>
  );
}

export default Checkout;