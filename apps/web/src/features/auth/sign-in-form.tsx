"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useQueryClient } from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import { useSearchParams } from "next/navigation";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { Field, Input, SubmitButton } from "@/components/form";
import { useRouter } from "@/i18n/navigation";
import { queryKeys } from "@/lib/query";

import { signIn } from "./api";
import { authErrorKey } from "./auth-error-message";

/** Removes the locale prefix: the locale-aware router adds it back. */
function stripLocale(path: string): string {
  const withoutLocale = path.replace(/^\/(en|uk)(?=\/|$)/, "");
  return withoutLocale || "/workspace";
}

export function SignInForm() {
  const t = useTranslations("auth");
  const router = useRouter();
  const queryClient = useQueryClient();
  const searchParams = useSearchParams();
  const [formError, setFormError] = useState<string | null>(null);

  // Messages come from the catalogue, so validation speaks the reader's
  // language too — an English "Required" under a Ukrainian label is jarring.
  const schema = z.object({
    email: z.email(t("emailInvalid")),
    password: z.string().min(1, t("passwordRequired")),
  });

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<z.infer<typeof schema>>({ resolver: zodResolver(schema) });

  const onSubmit = handleSubmit(async (values) => {
    setFormError(null);
    try {
      await signIn(values.email, values.password);
      // The session cookie changed what `me` returns, so the cached answer is
      // wrong until this is invalidated.
      await queryClient.invalidateQueries({ queryKey: queryKeys.auth.all });
      // Back to where they were headed before the redirect, if that is a path
      // inside this app. Anything else is an open redirect.
      const next = searchParams.get("next");
      const safe = next && next.startsWith("/") && !next.startsWith("//");
      router.push(safe ? stripLocale(next) : "/workspace");
    } catch (error) {
      setFormError(t(authErrorKey(error)));
    }
  });

  return (
    <form onSubmit={onSubmit} noValidate className="flex flex-col gap-4">
      {formError ? (
        <div role="alert" className="rounded-md border border-danger-subtle bg-danger-subtle p-3">
          <p className="text-sm font-medium text-danger">{formError}</p>
        </div>
      ) : null}

      <Field label={t("email")} error={errors.email?.message} required>
        {(props) => (
          <Input
            {...props}
            {...register("email")}
            type="email"
            autoComplete="email"
            // The first field on the page someone came here to use.
            autoFocus
          />
        )}
      </Field>

      <Field label={t("password")} error={errors.password?.message} required>
        {(props) => (
          <Input
            {...props}
            {...register("password")}
            type="password"
            autoComplete="current-password"
          />
        )}
      </Field>

      <SubmitButton pending={isSubmitting} pendingLabel={t("signInPending")}>
        {t("signInAction")}
      </SubmitButton>
    </form>
  );
}
