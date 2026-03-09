"use client";

import { useState, useEffect, useCallback } from "react";
import api from "@/lib/api";

interface NotificationItem {
  id: string;
  user_id: string;
  title: string;
  body: string;
  notification_type: string;
  channel: string;
  is_read: boolean;
  created_at: string;
  updated_at: string;
}

interface NotificationListData {
  items: NotificationItem[];
  unread_count: number;
}

export function useNotifications() {
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [loading, setLoading] = useState(false);

  const fetchUnreadCount = useCallback(async () => {
    try {
      const { data } = await api.get<{ unread_count: number }>("/notifications/unread-count");
      setUnreadCount(data.unread_count);
    } catch {
      // Non-critical, silently fail
    }
  }, []);

  const fetchNotifications = useCallback(async () => {
    setLoading(true);
    try {
      const { data } = await api.get<NotificationListData>("/notifications/", {
        params: { limit: 10 },
      });
      setNotifications(data.items);
      setUnreadCount(data.unread_count);
    } catch {
      // Silently fail
    } finally {
      setLoading(false);
    }
  }, []);

  const markAsRead = useCallback(async (ids: string[]) => {
    try {
      await api.patch("/notifications/mark-read", { notification_ids: ids });
      setNotifications((prev) =>
        prev.map((n) => (ids.includes(n.id) ? { ...n, is_read: true } : n)),
      );
      setUnreadCount((prev) => Math.max(0, prev - ids.length));
    } catch {
      // Silently fail
    }
  }, []);

  useEffect(() => {
    fetchUnreadCount();
    const interval = setInterval(fetchUnreadCount, 60_000);
    return () => clearInterval(interval);
  }, [fetchUnreadCount]);

  return { notifications, unreadCount, loading, fetchNotifications, fetchUnreadCount, markAsRead };
}
