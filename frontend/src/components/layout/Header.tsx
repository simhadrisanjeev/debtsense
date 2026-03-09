"use client";

import { useState, useRef, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Bell, ChevronDown, LogOut, User, Settings } from "lucide-react";
import { cn, formatRelativeTime } from "@/lib/utils";
import { clearAuth, getStoredUser, getRefreshToken } from "@/lib/auth";
import { authApi } from "@/lib/api";
import { useNotifications } from "@/hooks/useNotifications";

export function Header() {
  const router = useRouter();
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const [notificationsOpen, setNotificationsOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);
  const notifRef = useRef<HTMLDivElement>(null);
  const storedUser = getStoredUser();
  const displayName = storedUser
    ? `${storedUser.first_name} ${storedUser.last_name}`.trim()
    : "User";
  const initials = storedUser
    ? `${storedUser.first_name[0] ?? ""}${storedUser.last_name[0] ?? ""}`.toUpperCase()
    : "U";

  const { notifications, unreadCount, loading: notifLoading, fetchNotifications, markAsRead } = useNotifications();

  async function handleLogout() {
    setUserMenuOpen(false);
    try {
      const refreshToken = getRefreshToken();
      if (refreshToken) {
        await authApi.logout(refreshToken);
      }
    } catch {
      // best-effort revocation — clear locally regardless
    }
    clearAuth();
    router.push("/login");
  }

  // Close dropdowns when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setUserMenuOpen(false);
      }
      if (notifRef.current && !notifRef.current.contains(event.target as Node)) {
        setNotificationsOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  return (
    <header className="flex h-16 shrink-0 items-center justify-between border-b border-gray-200 bg-white px-6">
      {/* Left side - breadcrumb / page title area */}
      <div className="flex items-center gap-4">
        <h2 className="text-sm font-medium text-gray-500">
          Welcome back!
        </h2>
      </div>

      {/* Right side - notifications + user menu */}
      <div className="flex items-center gap-3">
        {/* Notifications */}
        <div className="relative" ref={notifRef}>
          <button
            onClick={() => {
              setNotificationsOpen(!notificationsOpen);
              if (!notificationsOpen) fetchNotifications();
              setUserMenuOpen(false);
            }}
            className="relative rounded-lg p-2 text-gray-500 hover:bg-gray-100 hover:text-gray-700"
          >
            <Bell className="h-5 w-5" />
            {unreadCount > 0 && (
              <span className="absolute right-1 top-1 flex h-4 w-4 items-center justify-center rounded-full bg-red-500 text-[10px] font-bold text-white">
                {unreadCount > 9 ? "9+" : unreadCount}
              </span>
            )}
          </button>

          {notificationsOpen && (
            <div className="absolute right-0 top-full mt-2 w-80 rounded-xl border border-gray-200 bg-white py-2 shadow-lg z-50">
              <div className="flex items-center justify-between px-4 py-2 border-b border-gray-100">
                <span className="text-sm font-semibold text-gray-900">Notifications</span>
                {notifications.some(n => !n.is_read) && (
                  <button
                    onClick={() => markAsRead(notifications.filter(n => !n.is_read).map(n => n.id))}
                    className="text-xs text-primary-600 hover:text-primary-700"
                  >
                    Mark all read
                  </button>
                )}
              </div>
              <div className="max-h-64 overflow-y-auto">
                {notifications.length === 0 ? (
                  <p className="px-4 py-6 text-center text-sm text-gray-500">No notifications</p>
                ) : (
                  notifications.map(n => (
                    <button
                      key={n.id}
                      onClick={() => { if (!n.is_read) markAsRead([n.id]); }}
                      className={`w-full text-left px-4 py-3 hover:bg-gray-50 ${!n.is_read ? "bg-primary-50/50" : ""}`}
                    >
                      <p className="text-sm font-medium text-gray-900">{n.title}</p>
                      <p className="text-xs text-gray-500 mt-0.5">{n.body}</p>
                      <p className="text-xs text-gray-400 mt-1">{formatRelativeTime(n.created_at)}</p>
                    </button>
                  ))
                )}
              </div>
            </div>
          )}
        </div>

        {/* User Menu */}
        <div className="relative" ref={menuRef}>
          <button
            type="button"
            onClick={() => {
              setUserMenuOpen((prev) => !prev);
              setNotificationsOpen(false);
            }}
            className="flex items-center gap-2 rounded-lg px-2 py-1.5 hover:bg-gray-100 transition-colors"
          >
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary-100 text-sm font-medium text-primary-700">
              {initials}
            </div>
            <span className="hidden text-sm font-medium text-gray-700 sm:block">
              {displayName}
            </span>
            <ChevronDown
              className={cn(
                "hidden h-4 w-4 text-gray-400 transition-transform sm:block",
                userMenuOpen && "rotate-180",
              )}
            />
          </button>

          {/* Dropdown */}
          {userMenuOpen && (
            <div className="absolute right-0 z-50 mt-1 w-48 rounded-lg border border-gray-200 bg-white py-1 shadow-lg">
              <Link
                href="/dashboard/settings"
                className="flex items-center gap-2 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
                onClick={() => setUserMenuOpen(false)}
              >
                <User className="h-4 w-4 text-gray-400" />
                Profile
              </Link>
              <Link
                href="/dashboard/settings"
                className="flex items-center gap-2 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
                onClick={() => setUserMenuOpen(false)}
              >
                <Settings className="h-4 w-4 text-gray-400" />
                Settings
              </Link>
              <div className="my-1 border-t border-gray-100" />
              <button
                type="button"
                className="flex w-full items-center gap-2 px-4 py-2 text-sm text-danger-600 hover:bg-danger-50"
                onClick={handleLogout}
              >
                <LogOut className="h-4 w-4" />
                Sign Out
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
