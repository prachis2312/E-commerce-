import { useState, useEffect } from "react";
import { Link, NavLink, useNavigate, useSearchParams, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { useCart } from "../context/CartContext";

const linkClass = ({ isActive }) => `nav-link${isActive ? " active" : ""}`;

function Navbar() {
  const { isAuthenticated, isAdmin, logout } = useAuth();
  const { itemCount } = useCart();
  const navigate = useNavigate();
  const location = useLocation();
  const [searchParams] = useSearchParams();

  // Keep the box in sync with the URL (?q=...), and empty it when leaving the products page.
  const urlQuery = location.pathname === "/products" ? searchParams.get("q") || "" : "";
  const [search, setSearch] = useState(urlQuery);
  useEffect(() => setSearch(urlQuery), [urlQuery]);

  const handleSearch = (e) => {
    e.preventDefault();
    const term = search.trim();
    navigate(term ? `/products?q=${encodeURIComponent(term)}` : "/products");
  };

  const handleLogout = async () => {
    await logout();
    navigate("/login");
  };

  return (
    <nav className="navbar">
      <div className="navbar-inner">
        <Link to="/products" className="brand">Shopfront</Link>

        <form className="search" onSubmit={handleSearch} role="search">
          <input
            className="input"
            type="search"
            placeholder="Search products"
            aria-label="Search products"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
          <button type="submit" className="btn btn-primary">Search</button>
        </form>

        <div className="nav-links">
          <NavLink to="/products" end className={linkClass}>Products</NavLink>
          {isAuthenticated ? (
            <>
              <NavLink to="/cart" className={linkClass}>
                Cart{itemCount > 0 && <span className="badge">{itemCount}</span>}
              </NavLink>
              <NavLink to="/orders" className={linkClass}>Orders</NavLink>
              {isAdmin && <NavLink to="/admin" className={linkClass}>Admin</NavLink>}
              <button className="btn btn-secondary btn-sm" onClick={handleLogout}>Log out</button>
            </>
          ) : (
            <>
              <Link to="/login" className="btn btn-ghost btn-sm">Log in</Link>
              <Link to="/register" className="btn btn-primary btn-sm">Sign up</Link>
            </>
          )}
        </div>
      </div>
    </nav>
  );
}

export default Navbar;
