import type { NotificationCategory } from "@newfan/contracts";

type NotificationLinkInput = {
  category: NotificationCategory;
  selectedId?: string;
  unreadOnly?: boolean;
};

export function buildNotificationCenterLink(input: NotificationLinkInput): string {
  const params = new URLSearchParams();
  params.set("tab", input.category);
  if (input.unreadOnly) {
    params.set("unread", "true");
  }
  if (input.selectedId) {
    params.set("selectedId", input.selectedId);
  }
  const query = params.toString();
  return `/notifications${query ? `?${query}` : ""}`;
}
