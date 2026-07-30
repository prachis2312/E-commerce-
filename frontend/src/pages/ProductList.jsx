import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { getProducts, getCategories } from "../api/products";
import ProductCard from "../components/ProductCard";
import { getRecommendationsForUser } from "../api/recommendations";
import { useAuth } from "../context/AuthContext";

const PAGE_SIZE = 20;

function ProductList() {
  const [products, setProducts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState("");
  const [skip, setSkip] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const { isAuthenticated, user } = useAuth();
  const [recommended, setRecommended] = useState([]);

  useEffect(() => {
    if (isAuthenticated && user?.user_id) {
      getRecommendationsForUser(user.user_id)
        .then((res) => setRecommended(res.data.recommendations))
        .catch(() => setRecommended([])); // fails silently — not core functionality
    } else {
      setRecommended([]);
    }
  }, [isAuthenticated, user]);

  // Fetch categories once on mount — used to populate the filter dropdown.
  useEffect(() => {
    getCategories()
      .then((res) => setCategories(res.data))
      .catch(() => {
        // Non-fatal: if categories fail to load, the page still works,
        // just without the filter dropdown options.
      });
  }, []);

  // Re-fetch products whenever the category filter or page (skip) changes.
  useEffect(() => {
    setLoading(true);
    setError("");

    getProducts({
      categoryId: selectedCategory || undefined,
      skip,
      limit: PAGE_SIZE,
    })
      .then((res) => setProducts(res.data))
      .catch(() => setError("Failed to load products."))
      .finally(() => setLoading(false));
  }, [selectedCategory, skip]);

  const handleCategoryChange = (e) => {
    setSelectedCategory(e.target.value);
    setSkip(0); // reset to first page whenever the filter changes
  };

  return (
    <div>
      <h2>Products</h2>

      {recommended.length > 0 && (
        <div style={{ marginBottom: "2rem" }}>
          <h3>Recommended for you</h3>
          <div style={{ display: "flex", flexWrap: "wrap", gap: "1rem" }}>
            {recommended.map((item) => (
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
                    stock_quantity: 1, // same simplification as Similar Products
                  }}
                />
              </Link>
            ))}
          </div>
        </div>
      )}

      <select value={selectedCategory} onChange={handleCategoryChange}>
        <option value="">All Categories</option>
        {categories.map((cat) => (
          <option key={cat.id} value={cat.id}>
            {cat.name}
          </option>
        ))}
      </select>

      {loading && <p>Loading...</p>}
      {error && <p style={{ color: "red" }}>{error}</p>}

      <div style={{ display: "flex", flexWrap: "wrap", gap: "1rem", marginTop: "1rem" }}>
        {products.map((product) => (
          <Link
            key={product.id}
            to={`/products/${product.id}`}
            style={{ textDecoration: "none", color: "inherit" }}
          >
            <ProductCard product={product} />
          </Link>
        ))}
      </div>

      {!loading && products.length === 0 && <p>No products found.</p>}

      <div style={{ marginTop: "1rem" }}>
        <button onClick={() => setSkip(Math.max(0, skip - PAGE_SIZE))} disabled={skip === 0}>
          Previous
        </button>
        <button
          onClick={() => setSkip(skip + PAGE_SIZE)}
          disabled={products.length < PAGE_SIZE}
          style={{ marginLeft: "0.5rem" }}
        >
          Next
        </button>
      </div>
    </div>
  );
}

export default ProductList;