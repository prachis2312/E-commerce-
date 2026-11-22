import { useState, useEffect } from "react";
import { useLocation, Link } from "react-router-dom";
import { getOrders } from "../api/orders";

const statusLabel = (value) => String(value).replace(/_/g, " ").toLowerCase();
const paymentClass = (value) => {
  const v = String(value).toLowerCase();
  if (v.includes("paid") || v.includes("success") || v.includes("complete")) return "pill pill-ok";
  if (v.includes("fail")) return "pill pill-bad";
  return "pill";
};

function Orders() {
  const location = useLocation();
  const justPlaced = location.state?.justPlaced;

  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    getOrders()
      .then((res) => setOrders(res.data))
      .catch(() => setError("Could not load your orders."))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="page page-medium">
      <h2>Your orders</h2>

      {justPlaced && (
        <div className="confirm-banner" role="status">
          <h3>Order placed</h3>
          <p>Order #{justPlaced.id} for ₹{justPlaced.total_amount} is confirmed.</p>
        </div>
      )}

      {loading && <p className="muted">Loading orders...</p>}
      {error && <div className="alert alert-error">{error}</div>}

      {!loading && !error && orders.length === 0 && (
        <div className="empty">
          <h3>No orders yet</h3>
          <p>When you place an order it will appear here.</p>
          <Link to="/products" className="btn btn-primary">Start shopping</Link>
        </div>
      )}

      {orders.map((order) => (
        <div key={order.id} className="panel order-card">
          <div className="order-head">
            <strong>Order #{order.id}</strong>
            <span className="muted">{new Date(order.created_at).toLocaleDateString()}</span>
          </div>
          <div>
            <span className="pill">{statusLabel(order.status)}</span>
            <span className={paymentClass(order.payment_status)}>payment {statusLabel(order.payment_status)}</span>
          </div>
          <ul className="order-items">
            {order.items.map((item) => (
              <li key={item.id}>{item.product_name} × {item.quantity} — ₹{item.price_at_order} each</li>
            ))}
          </ul>
          <strong>Total ₹{order.total_amount}</strong>
        </div>
      ))}
    </div>
  );
}

export default Orders;
