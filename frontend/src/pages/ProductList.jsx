import { useState, useEffect } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { getProducts, getCategories } from "../api/products";
import ProductCard from "../components/ProductCard";
import { getRecommendationsForUser } from "../api/recommendations";
import { useAuth } from "../context/AuthContext";

const PAGE_SIZE = 20;

function ProductList() {
  const [searchParams, setSearchParams] = useSearchParams();
  const query = searchParams.get("q") || "";
  const selectedCategory = searchParams.get("category") || "";

  const [products, setProducts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [skip, setSkip] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const { isAuthenticated, user } = useAuth();
  const [recommended, setRecommended] = useState([]);

  useEffect(() => {
    if (isAuthenticated && user?.user_id) {
      getRecommendationsForUser(user.user_id)
        .then((res) => setRecommended(res.data.recommendations))
        .catch(() => setRecommended([])); // not core functionality, fail quietly
    } else {
      setRecommended([]);
    }
  }, [isAuthenticated, user?.user_id]);

  useEffect(() => {
    getCategories().then((res) => setCategories(res.data)).catch(() => {});
  }, []);

  // New search or category -> back to page 1.
  useEffect(() => setSkip(0), [query, selectedCategory]);

  useEffect(() => {
    let cancelled = false; // ignore a slow response from an older search
    setLoading(true);
    setError("");

    getProducts({ q: query, categoryId: selectedCategory || undefined, skip, limit: PAGE_SIZE })
      .then((res) => { if (!cancelled) setProducts(res.data); })
      .catch(() => { if (!cancelled) setError("Could not load products. Please try again."); })
      .finally(() => { if (!cancelled) setLoading(false); });

    return () => { cancelled = true; };
  }, [query, selectedCategory, skip]);

  const updateParams = (changes) => {
    const next = new URLSearchParams(searchParams);
    Object.entries(changes).forEach(([key, value]) => (value ? next.set(key, value) : next.delete(key)));
    setSearchParams(next);
  };

  const showRecommended = recommended.length > 0 && !query && !selectedCategory;

  return (
    <div className="page">
      {showRecommended && (
        <section>
          <h2>Recommended for you</h2>
          <div className="product-grid">
            {recommended.map((item) => (
              <Link key={item.product_id} to={`/products/${item.product_id}`} className="product-link">
                <ProductCard product={{ name: item.name, price: item.price, image_url: item.image_url }} />
              </Link>
            ))}
          </div>
        </section>
      )}

      <div className="page-header" style={showRecommended ? { marginTop: "2.25rem" } : undefined}>
        <h2>{query ? `Results for “${query}”` : "All products"}</h2>
        <div className="toolbar" style={{ margin: 0 }}>
          {query && (
            <button className="btn btn-ghost btn-sm" onClick={() => updateParams({ q: "" })}>
              Clear search
            </button>
          )}
          <select
            className="select"
            aria-label="Filter by category"
            value={selectedCategory}
            onChange={(e) => updateParams({ category: e.target.value })}
          >
            <option value="">All categories</option>
            {categories.map((cat) => (
              <option key={cat.id} value={cat.id}>{cat.name}</option>
            ))}
          </select>
        </div>
      </div>

      {error && <div className="alert alert-error">{error}</div>}
      {loading && <p className="muted">Loading products...</p>}

      {!loading && !error && products.length === 0 && (
        <div className="empty">
          <h3>No products found</h3>
          <p>
            {query
              ? `Nothing matched “${query}”. Check the spelling or try a more general word.`
              : "There are no products in this category yet."}
          </p>
          <button className="btn btn-primary" onClick={() => setSearchParams({})}>
            Show all products
          </button>
        </div>
      )}

      <div className="product-grid">
        {products.map((product) => (
          <Link key={product.id} to={`/products/${product.id}`} className="product-link">
            <ProductCard product={product} />
          </Link>
        ))}
      </div>

      {(skip > 0 || products.length === PAGE_SIZE) && (
        <div className="pagination">
          <button className="btn btn-secondary" onClick={() => setSkip(Math.max(0, skip - PAGE_SIZE))} disabled={skip === 0}>
            Previous
          </button>
          <span className="muted">Page {skip / PAGE_SIZE + 1}</span>
          <button className="btn btn-secondary" onClick={() => setSkip(skip + PAGE_SIZE)} disabled={products.length < PAGE_SIZE}>
            Next
          </button>
        </div>
      )}
    </div>
  );
}

export default ProductList;
