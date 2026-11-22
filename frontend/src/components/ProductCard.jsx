// stock_quantity / category are optional: recommendation cards don't carry them,
// so we simply don't show stock info there instead of showing something wrong.
function ProductCard({ product }) {
  const stock = product.stock_quantity;
  const hasStock = typeof stock === "number";

  return (
    <div className="product-card">
      <div className="product-card-img">
        {product.image_url && <img src={product.image_url} alt={product.name} loading="lazy" />}
      </div>
      <div className="product-card-body">
        {product.category && <span className="chip">{product.category.name}</span>}
        <h4 className="product-card-name">{product.name}</h4>
        {hasStock && (
          <span className={`stock ${stock === 0 ? "stock-out" : stock <= 5 ? "stock-low" : "stock-in"}`}>
            {stock === 0 ? "Out of stock" : stock <= 5 ? `Only ${stock} left` : "In stock"}
          </span>
        )}
        <div className="product-card-price">₹{product.price}</div>
      </div>
    </div>
  );
}

export default ProductCard;
