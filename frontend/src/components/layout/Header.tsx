"use client";

import { useState, useRef, useEffect } from "react";
import Link from "next/link";
import { Bell, ChevronDown, LogOut, User, Settings } from "lucide-react";
import { cn } from "@/lib/utils";

export function Header() {
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  // Close the dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setUserMenuOpen(false);
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
        <button
          type="button"
          className="relative rounded-lg p-2 text-gray-400 hover:bg-gray-100 hover:text-gray-600 transition-colors"
          aria-label="View notifications"
        >
          <Bell className="h-5 w-5" />
          <span className="absolute right-1.5 top-1.5 h-2 w-2 rounded-full bg-danger-500" />
        </button>

        {/* User Menu */}
        <div className="relative" ref={menuRef}>
          <button
            type="button"
            onClick={() => setUserMenuOpen((prev) => !prev)}
            className="flex items-center gap-2 rounded-lg px-2 py-1.5 hover:bg-gray-100 transition-colors"
          >
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary-100 text-sm font-medium text-primary-700">
              U
            </div>
            <span className="hidden text-sm font-medium text-gray-700 sm:block">
              User
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
                onClick={() => {
                  setUserMenuOpen(false);
                  // logout logic would go here
                }}
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
