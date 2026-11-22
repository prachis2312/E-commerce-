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

const inputStyle = { display: "block", width: "100%", boxSizing: "border-box", padding: "0.4rem", marginBottom: "0.6rem" };

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
    <div style={{ maxWidth: 900, margin: "0 auto", padding: "1rem" }}>
      <h2>Admin Dashboard</h2>

      {message.text && (
        <p style={{ color: message.type === "error" ? "red" : "green" }}>{message.text}</p>
      )}

      <section style={{ border: "1px solid #ccc", padding: "1rem", marginBottom: "1.5rem" }}>
        <h3>{editingId ? `Edit product #${editingId}` : "Add a product"}</h3>
        <form onSubmit={handleSubmit}>
          <input style={inputStyle} name="name" placeholder="Name *" value={form.name} onChange={handleChange} required />
          <textarea style={inputStyle} name="description" placeholder="Description" value={form.description} onChange={handleChange} rows={3} />
          <div style={{ display: "flex", gap: "0.6rem" }}>
            <input style={inputStyle} name="price" type="number" step="0.01" min="0" placeholder="Price *" value={form.price} onChange={handleChange} required />
            <input style={inputStyle} name="stock_quantity" type="number" min="0" step="1" placeholder="Stock *" value={form.stock_quantity} onChange={handleChange} required />
          </div>
          <input style={inputStyle} name="image_url" placeholder="Image URL (optional)" value={form.image_url} onChange={handleChange} />
          <select style={inputStyle} name="category_id" value={form.category_id} onChange={handleChange}>
            <option value="">No category</option>
            {categories.map((c) => (
              <option key={c.id} value={c.id}>{c.name}</option>
            ))}
          </select>
          <button type="submit" disabled={saving}>
            {saving ? "Saving..." : editingId ? "Save changes" : "Add product"}
          </button>
          {editingId && (
            <button type="button" onClick={resetForm} style={{ marginLeft: "0.5rem" }}>Cancel edit</button>
          )}
        </form>

        <form onSubmit={handleAddCategory} style={{ marginTop: "1rem" }}>
          <input
            placeholder="New category name"
            value={newCategory}
            onChange={(e) => setNewCategory(e.target.value)}
            style={{ padding: "0.4rem" }}
          />
          <button type="submit" style={{ marginLeft: "0.5rem" }}>Add category</button>
        </form>
      </section>

      <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
        <h3 style={{ margin: 0 }}>Products</h3>
        <button onClick={handleRefreshRecommendations} disabled={refreshing}>
          {refreshing ? "Refreshing..." : "Refresh recommendations"}
        </button>
        <small>(Happens automatically after add/edit/delete; use this if recommendations look stale.)</small>
      </div>
      <table style={{ width: "100%", borderCollapse: "collapse" }}>
        <thead>
          <tr style={{ textAlign: "left", borderBottom: "2px solid #ccc" }}>
            <th>ID</th><th>Name</th><th>Category</th><th>Price</th><th>Stock</th><th></th>
          </tr>
        </thead>
        <tbody>
          {products.map((p) => (
            <tr key={p.id} style={{ borderBottom: "1px solid #eee" }}>
              <td>{p.id}</td>
              <td>{p.name}</td>
              <td>{p.category?.name || "-"}</td>
              <td>${p.price}</td>
              <td style={{ color: p.stock_quantity === 0 ? "red" : "inherit" }}>{p.stock_quantity}</td>
              <td>
                <button onClick={() => handleEdit(p)}>Edit</button>
                <button onClick={() => handleDelete(p)} style={{ marginLeft: "0.4rem" }}>Delete</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {products.length === 0 && <p>No products on this page.</p>}

      <div style={{ marginTop: "1rem" }}>
        <button onClick={() => setSkip(Math.max(0, skip - PAGE_SIZE))} disabled={skip === 0}>Previous</button>
        <button onClick={() => setSkip(skip + PAGE_SIZE)} disabled={products.length < PAGE_SIZE} style={{ marginLeft: "0.5rem" }}>Next</button>
      </div>
    </div>
  );
}

export default Admin;
