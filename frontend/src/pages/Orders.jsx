import { useState, useEffect } from "react";
import { useLocation, Link } from "react-router-dom";
import { getOrders } from "../api/orders";

function Orders() {
  const location = useLocation();
  const justPlaced = location.state?.justPlaced;

  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    getOrders()
      .then((res) => setOrders(res.data))
      .catch(() => setError("Failed to load orders."))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div>
      <h2>Your Orders</h2>

      {justPlaced && (
        <div style={{ border: "2px solid green", padding: "1rem", marginBottom: "1rem" }}>
          <h3>Order Confirmed! 🎉</h3>
          <p>Order #{justPlaced.id} — ₹{justPlaced.total_amount}</p>
          <p>Status: {justPlaced.status} | Payment: {justPlaced.payment_status}</p>
        </div>
      )}

      {loading && <p>Loading...</p>}
      {error && <p style={{ color: "red" }}>{error}</p>}

      {!loading && orders.length === 0 && (
        <p>No orders yet. <Link to="/products">Start shopping</Link></p>
      )}

      {orders.map((order) => (
        <div key={order.id} style={{ border: "1px solid #444", padding: "1rem", marginBottom: "1rem" }}>
          <p><strong>Order #{order.id}</strong> — {new Date(order.created_at).toLocaleDateString()}</p>
          <p>Status: {order.status} | Payment: {order.payment_status}</p>
          <ul>
            {order.items.map((item) => (
              <li key={item.id}>
                {item.product_name} × {item.quantity} — ₹{item.price_at_order} each
              </li>
            ))}
          </ul>
          <p><strong>Total: ₹{order.total_amount}</strong></p>
        </div>
      ))}
    </div>
  );
}

export default Orders;