import { useState, useEffect, useCallback } from "react";
import {
  getProducts, getCategories,
  createProduct, updateProduct, deleteProduct, createCategory,
} from "../api/products";
import { refreshRecommendations } from "../api/recommendations";

const EMPTY_FORM = {
  name: "", description: "", price: "", stock_quantity: "", image_url: "", category_id: "",
};

const PAGE_SIZE = 20;

function Admin() {
  const [products, setProducts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [skip, setSkip] = useState(0);
  const [form, setForm] = useState(EMPTY_FORM);
  const [editingId, setEditingId] = useState(null);
  const [newCategory, setNewCategory] = useState("");
  const [message, setMessage] = useState({ type: "", text: "" });
  const [saving, setSaving] = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  const loadProducts = useCallback(() => {
    return getProducts({ skip, limit: PAGE_SIZE })
      .then((res) => setProducts(res.data))
      .catch(() => setMessage({ type: "error", text: "Failed to load products." }));
  }, [skip]);

  const loadCategories = () =>
    getCategories().then((res) => setCategories(res.data)).catch(() => {});

  useEffect(() => { loadProducts(); }, [loadProducts]);
  useEffect(() => { loadCategories(); }, []);

  const errorText = (err, fallback) => {
    const detail = err.response?.data?.detail;
    if (err.response?.status === 403) return "You do not have admin permission.";
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail)) return detail.map((d) => `${d.loc?.slice(-1)[0]}: ${d.msg}`).join("; ");
    return fallback;
  };

  const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  const resetForm = () => { setForm(EMPTY_FORM); setEditingId(null); };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setMessage({ type: "", text: "" });
    setSaving(true);

    const payload = {
      name: form.name.trim(),
      description: form.description.trim() || null,
      price: parseFloat(form.price),
      stock_quantity: parseInt(form.stock_quantity, 10),
      image_url: form.image_url.trim() || null,
      category_id: form.category_id ? parseInt(form.category_id, 10) : null,
    };

    if (!payload.name || Number.isNaN(payload.price) || payload.price < 0 || Number.isNaN(payload.stock_quantity) || payload.stock_quantity < 0) {
      setMessage({ type: "error", text: "Name, a non-negative price and a non-negative stock are required." });
      setSaving(false);
      return;
    }

    try {
      if (editingId) {
        await updateProduct(editingId, payload);
        setMessage({ type: "ok", text: "Product updated." });
      } else {
        await createProduct(payload);
        setMessage({ type: "ok", text: "Product added." });
      }
      resetForm();
      await loadProducts();
    } catch (err) {
      setMessage({ type: "error", text: errorText(err, "Could not save the product.") });
    } finally {
      setSaving(false);
    }
  };

  const handleEdit = (p) => {
    setEditingId(p.id);
    setForm({
      name: p.name,
      description: p.description || "",
      price: String(p.price),
      stock_quantity: String(p.stock_quantity),
      image_url: p.image_url || "",
      category_id: p.category?.id ? String(p.category.id) : "",
    });
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const handleDelete = async (p) => {
    if (!window.confirm(`Delete "${p.name}"? This cannot be undone.`)) return;
    try {
      await deleteProduct(p.id);
      setMessage({ type: "ok", text: `Deleted "${p.name}".` });
      if (editingId === p.id) resetForm();
      await loadProducts();
    } catch (err) {
      setMessage({ type: "error", text: errorText(err, "Could not delete the product.") });
    }
  };

  const handleRefreshRecommendations = async () => {
    setRefreshing(true);
    try {
      const res = await refreshRecommendations();
      setMessage({ type: "ok", text: `Recommendations updated (${res.data.embeddings_processed} product(s) re-embedded).` });
    } catch (err) {
      setMessage({ type: "error", text: errorText(err, "Could not refresh recommendations.") });
    } finally {
      setRefreshing(false);
    }
  };

  const handleAddCategory = async (e) => {
    e.preventDefault();
    if (!newCategory.trim()) return;
    try {
      await createCategory({ name: newCategory.trim() });
      setNewCategory("");
      setMessage({ type: "ok", text: "Category added." });
      await loadCategories();
    } catch (err) {
      setMessage({ type: "error", text: errorText(err, "Could not add the category.") });
    }
  };

  return (
    <div className="page">
      <div className="page-header">
        <h2>Admin dashboard</h2>
      </div>

      {message.text && (
        <div className={`alert ${message.type === "error" ? "alert-error" : "alert-success"}`} role="status">
          {message.text}
        </div>
      )}

      <div className="admin-grid">
        <section className="panel">
          <h3>{editingId ? `Edit product #${editingId}` : "Add a product"}</h3>
          <form onSubmit={handleSubmit}>
            <div className="field">
              <label htmlFor="name">Name</label>
              <input id="name" className="input" name="name" value={form.name} onChange={handleChange} required />
            </div>
            <div className="field">
              <label htmlFor="description">Description</label>
              <textarea id="description" className="textarea" name="description" rows={3} value={form.description} onChange={handleChange} />
            </div>
            <div className="form-row">
              <div className="field">
                <label htmlFor="price">Price (₹)</label>
                <input id="price" className="input" name="price" type="number" step="0.01" min="0" value={form.price} onChange={handleChange} required />
              </div>
              <div className="field">
                <label htmlFor="stock_quantity">Stock</label>
                <input id="stock_quantity" className="input" name="stock_quantity" type="number" min="0" step="1" value={form.stock_quantity} onChange={handleChange} required />
              </div>
            </div>
            <div className="field">
              <label htmlFor="image_url">Image URL (optional)</label>
              <input id="image_url" className="input" name="image_url" value={form.image_url} onChange={handleChange} />
            </div>
            <div className="field">
              <label htmlFor="category_id">Category</label>
              <select id="category_id" className="select" name="category_id" value={form.category_id} onChange={handleChange}>
                <option value="">No category</option>
                {categories.map((c) => (
                  <option key={c.id} value={c.id}>{c.name}</option>
                ))}
              </select>
            </div>
            <div className="actions" style={{ justifyContent: "flex-start", marginTop: 0 }}>
              <button type="submit" className="btn btn-primary" disabled={saving}>
                {saving ? "Saving..." : editingId ? "Save changes" : "Add product"}
              </button>
              {editingId && (
                <button type="button" className="btn btn-secondary" onClick={resetForm}>Cancel</button>
              )}
            </div>
          </form>
        </section>

        <section className="panel">
          <h3>Add a category</h3>
          <form onSubmit={handleAddCategory} className="form-row" style={{ alignItems: "flex-end" }}>
            <div className="field" style={{ marginBottom: 0 }}>
              <label htmlFor="new-category">Category name</label>
              <input id="new-category" className="input" value={newCategory} onChange={(e) => setNewCategory(e.target.value)} />
            </div>
            <button type="submit" className="btn btn-secondary" style={{ flex: "none" }}>Add category</button>
          </form>
        </section>
      </div>

      <div className="page-header">
        <h3 style={{ margin: 0 }}>Products</h3>
        <div className="toolbar" style={{ margin: 0 }}>
          <span className="muted">Recommendations update automatically.</span>
          <button className="btn btn-secondary btn-sm" onClick={handleRefreshRecommendations} disabled={refreshing}>
            {refreshing ? "Refreshing..." : "Refresh recommendations"}
          </button>
        </div>
      </div>

      <div className="table-wrap">
        <table className="table">
          <thead>
            <tr><th>ID</th><th>Name</th><th>Category</th><th>Price</th><th>Stock</th><th></th></tr>
          </thead>
          <tbody>
            {products.map((p) => (
              <tr key={p.id}>
                <td className="table-id">{p.id}</td>
                <td>{p.name}</td>
                <td>{p.category?.name || "-"}</td>
                <td>₹{p.price}</td>
                <td className={p.stock_quantity === 0 ? "stock-out" : ""}>{p.stock_quantity}</td>
                <td>
                  <div className="row-actions">
                    <button className="btn btn-secondary btn-sm" onClick={() => handleEdit(p)}>Edit</button>
                    <button className="btn btn-danger btn-sm" onClick={() => handleDelete(p)}>Delete</button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {products.length === 0 && <p className="muted" style={{ marginTop: "0.75rem" }}>No products on this page.</p>}

      <div className="pagination">
        <button className="btn btn-secondary" onClick={() => setSkip(Math.max(0, skip - PAGE_SIZE))} disabled={skip === 0}>Previous</button>
        <span className="muted">Page {skip / PAGE_SIZE + 1}</span>
        <button className="btn btn-secondary" onClick={() => setSkip(skip + PAGE_SIZE)} disabled={products.length < PAGE_SIZE}>Next</button>
      </div>
    </div>
  );
}

export default Admin;
