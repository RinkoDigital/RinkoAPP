import { NavLink } from "react-router-dom";
import { useTranslation } from "react-i18next";

export function BottomNav() {
  const { t } = useTranslation();
  return (
    <nav className="bottom-nav">
      <NavLink to="/" end className={({ isActive }) => (isActive ? "active" : "")}>
        {t("nav.home")}
      </NavLink>
      <NavLink to="/ledger" className={({ isActive }) => (isActive ? "active" : "")}>
        {t("nav.ledger")}
      </NavLink>
      <NavLink to="/account" className={({ isActive }) => (isActive ? "active" : "")}>
        {t("nav.account")}
      </NavLink>
    </nav>
  );
}
