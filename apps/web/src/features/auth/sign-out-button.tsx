"use client";

import { useQueryClient } from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import { useTransition } from "react";

import { useRouter } from "@/i18n/navigation";

import { signOut } from "./api";

export function SignOutButton() {
  const t = useTranslations("auth");
  const router = useRouter();
  const queryClient = useQueryClient();
  const [isPending, startTransition] = useTransition();

  const onClick = () => {
    startTransition(async () => {
      try {
        await signOut();
      } finally {
        // Even if the call failed, the cookies may be gone and the cache is
        // certainly wrong. Clearing it stops the next page rendering someone
        // who is no longer signed in.
        queryClient.clear();
        router.push("/sign-in");
        // The layout is a Server Component, so its copy of the user is stale
        // until the route cache is refreshed.
        router.refresh();
      }
    });
  };

  return (
    <button
      type="button"
      onClick={onClick}
      disabled={isPending}
      className="rounded-md px-2.5 py-1.5 text-sm font-medium text-text-muted transition-colors duration-fast hover:bg-surface-muted hover:text-text disabled:opacity-60"
    >
      {t("signOut")}
    </button>
  );
}
