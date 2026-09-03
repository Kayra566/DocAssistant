import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { notificationApi } from "@/features/system/api";

export function NotificationBell() {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const [open, setOpen] = useState(false);

  const countQuery = useQuery({
    queryKey: ["notifications-unread"],
    queryFn: notificationApi.unreadCount,
    refetchInterval: 60_000,
  });

  const listQuery = useQuery({
    queryKey: ["notifications"],
    queryFn: notificationApi.list,
    enabled: open,
  });

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ["notifications"] });
    queryClient.invalidateQueries({ queryKey: ["notifications-unread"] });
  };

  const readMutation = useMutation({
    mutationFn: (id: string) => notificationApi.markRead(id),
    onSuccess: invalidate,
  });

  const readAllMutation = useMutation({
    mutationFn: notificationApi.markAllRead,
    onSuccess: invalidate,
  });

  const unread = countQuery.data ?? 0;

  return (
    <div className="relative">
      <button
        type="button"
        aria-label={t("notifications.unreadLabel", { count: unread })}
        aria-expanded={open}
        onClick={() => setOpen((value) => !value)}
        className="relative rounded-md px-2 py-1 text-neutral-300 hover:bg-neutral-800 focus:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500"
      >
        <span aria-hidden="true">🔔</span>
        {unread > 0 && (
          <span className="absolute -right-1 -top-1 rounded-full bg-indigo-600 px-1.5 text-[10px] font-semibold text-white">
            {unread > 9 ? "9+" : unread}
          </span>
        )}
      </button>

      {open && (
        <div
          role="dialog"
          aria-label={t("notifications.title")}
          className="absolute right-0 z-40 mt-2 w-80 space-y-2 rounded-xl border border-neutral-800 bg-neutral-900 p-3 shadow-xl"
        >
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold">{t("notifications.title")}</h2>
            {unread > 0 && (
              <Button
                variant="ghost"
                className="px-2 py-1 text-xs"
                onClick={() => readAllMutation.mutate()}
              >
                {t("notifications.markAllRead")}
              </Button>
            )}
          </div>

          {listQuery.data?.length === 0 && (
            <p className="text-xs text-neutral-500">{t("notifications.empty")}</p>
          )}

          <ul className="max-h-80 space-y-1 overflow-y-auto">
            {listQuery.data?.map((item) => (
              <li key={item.id}>
                <Link
                  to={item.link ?? "/dashboard"}
                  onClick={() => {
                    if (!item.read) readMutation.mutate(item.id);
                    setOpen(false);
                  }}
                  className={`block rounded-md border px-3 py-2 text-xs hover:border-neutral-600 ${
                    item.read
                      ? "border-neutral-800 text-neutral-400"
                      : "border-indigo-800 bg-indigo-950/30 text-neutral-200"
                  }`}
                >
                  <p className="font-medium">{item.title}</p>
                  <p className="text-neutral-500">{item.body}</p>
                </Link>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
