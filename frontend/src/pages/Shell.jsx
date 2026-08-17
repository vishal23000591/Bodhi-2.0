import { Outlet } from "react-router-dom";
import Sidebar from "../components/Sidebar";

export default function Shell() {
  return (
    <div className="app-shell">
      <Sidebar />
      <div className="main-panel">
        <Outlet />
      </div>
    </div>
  );
}
