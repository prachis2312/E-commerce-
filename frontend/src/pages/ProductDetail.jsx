import { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import { getProduct } from "../api/products";
import { getSimilarProducts } from "../api/recommendations";
import ProductCard from "../components/ProductCard";
import { useCart } from "../context/CartContext";
import { useNavigate } from "react-router-dom";


function ProductDetail() {
  const { productId } = useParams();
  const [product, setProduct] = useState(null);
  const [similar, setSimilar] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const { addItem } = useCart();
  const [addError, setAddError] = useState("");
  const [adding, setAdding] = useState(false);

  const navigate = useNavigate();
  const [quantity, setQuantity] = useState(1);





  const handleBuyNow = () => {
    navigate("/checkout", {
      state: { buyNowProduct: { product, quantity } },
    });
  };

  useEffect(() => {
    setLoading(true);
    setError("");
    setQuantity(1);

    getProduct(productId)
      .then((res) => setProduct(res.data))
      .catch(() => setError("Product not found."))
      .finally(() => setLoading(false));

    getSimilarProducts(productId)
      .then((res) => setSimilar(res.data.recommendations))
      .catch(() => setSimilar([]));
  }, [productId]);

  const handleAddToCart = async () => {
    setAddError("");
    setAdding(true);
    try {
      await addItem(product.id, quantity);
    } catch (err) {
      if (err.response && err.response.data && err.response.data.detail) {
        setAddError(err.response.data.detail);
      } else {
        setAddError("Could not add to cart.");
      }
    } finally {
      setAdding(false);
    }
  };

  if (loading) return <div className="page"><p className="muted">Loading product...</p></div>;
  if (error) {
    return (
      <div className="page">
        <div className="alert alert-error">{error}</div>
        <Link to="/products" className="btn btn-secondary">Back to products</Link>
      </div>
    );
  }
  if (!product) return null;

  const inStock = product.stock_quantity > 0;

  return (
    <div className="page">
      <Link to="/products" className="back-link">← Back to products</Link>

      <div className="detail">
        <div className="detail-img">
          {product.image_url && <img src={product.image_url} alt={product.name} />}
        </div>

        <div>
          {product.category && <span className="chip">{product.category.name}</span>}
          <h2 style={{ marginTop: "0.5rem" }}>{product.name}</h2>
          <div className="detail-price">₹{product.price}</div>
          <span className={`stock ${!inStock ? "stock-out" : product.stock_quantity <= 5 ? "stock-low" : "stock-in"}`}>
            {!inStock ? "Out of stock" : product.stock_quantity <= 5 ? `Only ${product.stock_quantity} left` : `In stock (${product.stock_quantity} available)`}
          </span>
          <p className="detail-desc">{product.description}</p>

          {inStock && (
            <div className="buy-row">
              <label className="qty">
                Quantity
                <input
                  className="input input-qty"
                  type="number"
                  min="1"
                  max={product.stock_quantity}
                  value={quantity}
                  onChange={(e) => {
                    const val = parseInt(e.target.value) || 1;
                    setQuantity(Math.min(Math.max(val, 1), product.stock_quantity));
                  }}
                />
              </label>
            </div>
          )}

          <div className="buy-row">
            <button className="btn btn-primary" onClick={handleAddToCart} disabled={!inStock || adding}>
              {adding ? "Adding..." : "Add to cart"}
            </button>
            <button className="btn btn-secondary" onClick={handleBuyNow} disabled={!inStock}>
              Buy now
            </button>
          </div>
          {addError && <div className="alert alert-error">{addError}</div>}
        </div>
      </div>

      {similar.length > 0 && (
        <section>
          <h3 className="section-title">Similar products</h3>
          <div className="product-grid">
            {similar.map((item) => (
              <Link key={item.product_id} to={`/products/${item.product_id}`} className="product-link">
                <ProductCard product={{ name: item.name, price: item.price, image_url: item.image_url }} />
              </Link>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}

export default ProductDetail;
