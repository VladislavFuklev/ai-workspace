/**
 * Query keys, in one place.
 *
 * A key typed as a literal at the call site is a cache miss waiting to happen:
 * `["documents"]` and `["document"]` look alike in review and behave nothing
 * alike. Building them here means an invalidation cannot miss its own query.
 *
 * The hierarchy matters. `queryKeys.documents.all` is a prefix of every document
 * key, so invalidating it invalidates the list and every detail at once.
 */
export const queryKeys = {
  documents: {
    all: ["documents"] as const,
    list: (filters: { search?: string; page?: number } = {}) =>
      [...queryKeys.documents.all, "list", filters] as const,
    detail: (documentId: string) => [...queryKeys.documents.all, "detail", documentId] as const,
  },
  conversations: {
    all: ["conversations"] as const,
    list: () => [...queryKeys.conversations.all, "list"] as const,
    detail: (conversationId: string) =>
      [...queryKeys.conversations.all, "detail", conversationId] as const,
  },
  organizations: {
    all: ["organizations"] as const,
    current: () => [...queryKeys.organizations.all, "current"] as const,
    members: (organizationId: string) =>
      [...queryKeys.organizations.all, organizationId, "members"] as const,
  },
  usage: {
    all: ["usage"] as const,
    summary: (period: string) => [...queryKeys.usage.all, "summary", period] as const,
  },
} as const;
