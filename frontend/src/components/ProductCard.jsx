function ProductCard({ product }) {
  return (
    <div style={{ border: "1px solid #ccc", padding: "1rem", width: "220px" }}>
      {product.image_url && (
        <img
          src={product.image_url}
          alt={product.name}
          style={{ width: "100%", height: "150px", objectFit: "contain" }}
        />
      )}
      <h4>{product.name}</h4>
      <p>{product.category ? product.category.name : "Uncategorized"}</p>
      <p><strong>₹{product.price}</strong></p>
      <p style={{ color: product.stock_quantity > 0 ? "green" : "red" }}>
        {product.stock_quantity > 0 ? `In stock (${product.stock_quantity})` : "Out of stock"}
      </p>
    </div>
  );
}

export default ProductCard;