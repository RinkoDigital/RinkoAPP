import { NavLink } from "react-router-dom";

export function BottomNav() {
  return (
    <nav className="bottom-nav">
      <NavLink to="/" end className={({ isActive }) => (isActive ? "active" : "")}>
        Home
      </NavLink>
      <NavLink to="/ledger" className={({ isActive }) => (isActive ? "active" : "")}>
        Ledger
      </NavLink>
      <NavLink to="/account" className={({ isActive }) => (isActive ? "active" : "")}>
        Account
      </NavLink>
    </nav>
  );
}
