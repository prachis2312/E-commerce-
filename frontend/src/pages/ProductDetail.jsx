import { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import { getProduct } from "../api/products";
import { getSimilarProducts } from "../api/recommendations";
import ProductCard from "../components/ProductCard";
import { useCart } from "../context/CartContext";
import { buyNow } from "../api/orders";
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
  const [buyingNow, setBuyingNow] = useState(false);

  const handleBuyNow = () => {
    navigate("/checkout", {
      state: { buyNowProduct: { product, quantity: 1 } },
    });
  };

  useEffect(() => {
    setLoading(true);
    setError("");

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
      await addItem(product.id, 1);
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

  if (loading) return <p>Loading...</p>;
  if (error) return <p style={{ color: "red" }}>{error}</p>;
  if (!product) return null;

  return (
    <div>
      <Link to="/products">← Back to Products</Link>

      <div style={{ display: "flex", gap: "2rem", marginTop: "1rem" }}>
        {product.image_url && (
          <img src={product.image_url} alt={product.name} style={{ width: "300px", objectFit: "contain" }} />
        )}
        <div>
          <h2>{product.name}</h2>
          <p>{product.category ? product.category.name : "Uncategorized"}</p>
          <p><strong>₹{product.price}</strong></p>
          <p style={{ color: product.stock_quantity > 0 ? "green" : "red" }}>
            {product.stock_quantity > 0 ? `In stock (${product.stock_quantity})` : "Out of stock"}
          </p>
          <p>{product.description}</p>

          <button onClick={handleAddToCart} disabled={product.stock_quantity === 0 || adding}>
            {adding ? "Adding..." : "Add to Cart"}
          </button>
          <button onClick={handleBuyNow} disabled={product.stock_quantity === 0} style={{ marginLeft: "0.5rem" }}>
            Buy Now
          </button>
          {addError && <p style={{ color: "red" }}>{addError}</p>}
        </div>
      </div>

      {similar.length > 0 && (
        <div style={{ marginTop: "2rem" }}>
          <h3>Similar Products</h3>
          <div style={{ display: "flex", flexWrap: "wrap", gap: "1rem" }}>
            {similar.map((item) => (
              <Link
                key={item.product_id}
                to={`/products/${item.product_id}`}
                style={{ textDecoration: "none", color: "inherit" }}
              >
                <ProductCard
                  product={{
                    name: item.name,
                    price: item.price,
                    image_url: item.image_url,
                    stock_quantity: 1,
                  }}
                />
              </Link>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default ProductDetail;