type MessageLinkInput = {
  tab?: "all" | "dm" | "applications" | "teams";
  q?: string;
  unreadOnly?: boolean;
  threadId?: string;
};

export function buildMessagesLink(input: MessageLinkInput = {}): string {
  const params = new URLSearchParams();
  if (input.tab && input.tab !== "all") {
    params.set("tab", input.tab);
  }
  if (input.q?.trim()) {
    params.set("q", input.q.trim());
  }
  if (input.unreadOnly) {
    params.set("unread", "true");
  }
  if (input.threadId) {
    params.set("threadId", input.threadId);
  }
  const query = params.toString();
  return `/messages${query ? `?${query}` : ""}`;
}
