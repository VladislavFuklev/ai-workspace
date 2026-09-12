"use client";

import { QueryClientProvider } from "@tanstack/react-query";
import { useState } from "react";

import { createQueryClient } from "./client";

/**
 * One QueryClient per browser session, created in state rather than at module
 * scope: a module-level client is shared between requests on the server, which
 * would leak one user's cached data into another's render.
 */
export function QueryProvider({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(createQueryClient);
  return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
}
