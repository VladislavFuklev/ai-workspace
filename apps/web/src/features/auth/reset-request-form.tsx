"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useTranslations } from "next-intl";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { Field, Input, SubmitButton } from "@/components/form";

import { requestPasswordReset } from "./api";
import { authErrorKey } from "./auth-error-message";

export function ResetRequestForm() {
  const t = useTranslations("auth");
  const [sent, setSent] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const schema = z.object({ email: z.email(t("emailInvalid")) });

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<z.infer<typeof schema>>({ resolver: zodResolver(schema) });

  const onSubmit = handleSubmit(async (values) => {
    setFormError(null);
    try {
      await requestPasswordReset(values.email);
      // The same confirmation whichever it was: the endpoint refuses to say,
      // and so must the screen.
      setSent(true);
    } catch (error) {
      setFormError(t(authErrorKey(error)));
    }
  });

  if (sent) {
    return (
      <div role="status" className="rounded-lg border border-border bg-surface p-4">
        <p className="text-sm text-text">{t("resetSent")}</p>
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

      <Field label={t("email")} error={errors.email?.message} required>
        {(props) => (
          <Input {...props} {...register("email")} type="email" autoComplete="email" autoFocus />
        )}
      </Field>

      <SubmitButton pending={isSubmitting} pendingLabel={t("resetPending")}>
        {t("resetAction")}
      </SubmitButton>
    </form>
  );
}
