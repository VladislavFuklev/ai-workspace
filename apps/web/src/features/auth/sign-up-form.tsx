"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useTranslations } from "next-intl";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { Field, Input, SubmitButton, applyServerErrors } from "@/components/form";

import { register as registerAccount } from "./api";
import { authErrorKey } from "./auth-error-message";
import { MIN_PASSWORD_LENGTH } from "./schemas";

export function SignUpForm() {
  const t = useTranslations("auth");
  const [formError, setFormError] = useState<string | null>(null);
  const [done, setDone] = useState(false);

  const schema = z.object({
    display_name: z.string().min(1, t("nameRequired")),
    email: z.email(t("emailInvalid")),
    password: z
      .string()
      .min(MIN_PASSWORD_LENGTH, t("passwordTooShort", { min: MIN_PASSWORD_LENGTH })),
  });
  type Values = z.infer<typeof schema>;
  const FIELDS = ["display_name", "email", "password"] as const;

  const {
    register,
    handleSubmit,
    setError,
    formState: { errors, isSubmitting },
  } = useForm<Values>({ resolver: zodResolver(schema) });

  const onSubmit = handleSubmit(async (values) => {
    setFormError(null);
    try {
      await registerAccount(values.email, values.password, values.display_name);
      // Deliberately the same outcome whether or not the address was taken
      // (ADR-018) — the UI must not undo that by behaving differently.
      setDone(true);
    } catch (error) {
      // The API's policy can be stricter than the browser's; a 422 comes back
      // with the field named, and belongs on that field.
      if (!applyServerErrors(error, setError, FIELDS)) {
        setFormError(t(authErrorKey(error)));
      }
    }
  });

  if (done) {
    return (
      <div role="status" className="rounded-lg border border-border bg-surface p-4">
        <p className="text-sm text-text">{t("registered")}</p>
      </div>
    );
  }

  return (
    <form onSubmit={onSubmit} noValidate className="flex flex-col gap-4">
      {formError ? (
        <div role="alert" className="rounded-md border border-danger-subtle bg-danger-subtle p-3">
          <p className="text-sm font-medium text-danger">{formError}</p>
        </div>
      ) : null}

      <Field label={t("displayName")} error={errors.display_name?.message} required>
        {(props) => (
          <Input {...props} {...register("display_name")} autoComplete="name" autoFocus />
        )}
      </Field>

      <Field label={t("email")} error={errors.email?.message} required>
        {(props) => <Input {...props} {...register("email")} type="email" autoComplete="email" />}
      </Field>

      <Field
        label={t("password")}
        description={t("passwordHint", { min: MIN_PASSWORD_LENGTH })}
        error={errors.password?.message}
        required
      >
        {(props) => (
          <Input {...props} {...register("password")} type="password" autoComplete="new-password" />
        )}
      </Field>

      <SubmitButton pending={isSubmitting} pendingLabel={t("signUpPending")}>
        {t("signUpAction")}
      </SubmitButton>
    </form>
  );
}
