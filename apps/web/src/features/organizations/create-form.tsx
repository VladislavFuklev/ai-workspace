"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useTranslations } from "next-intl";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { Field, Input, SubmitButton, applyServerErrors } from "@/components/form";
import { useRouter } from "@/i18n/navigation";

import { createOrganization } from "./api";
import { MAX_ORGANIZATION_NAME } from "./schemas";

/**
 * Creates an organisation and goes straight into it.
 *
 * The address is derived from the name by the API, not chosen here: the rules
 * (transliteration, collisions, reserved words) live where the uniqueness is
 * enforced, and a slug field would let someone pick one that is about to be
 * taken.
 */
export function CreateOrganizationForm() {
  const t = useTranslations("organizations");
  const router = useRouter();
  const [formError, setFormError] = useState<string | null>(null);

  const schema = z.object({
    name: z.string().trim().min(1, t("nameRequired")).max(MAX_ORGANIZATION_NAME, t("nameTooLong")),
  });

  const {
    register,
    handleSubmit,
    setError,
    formState: { errors, isSubmitting },
  } = useForm<z.infer<typeof schema>>({ resolver: zodResolver(schema) });

  const onSubmit = handleSubmit(async (values) => {
    setFormError(null);
    try {
      const organization = await createOrganization(values.name);
      // `refresh` first: the server-rendered list and switcher above this form
      // are now stale, and the new organisation is where we are going.
      router.refresh();
      router.push(`/${organization.slug}/workspace`);
    } catch (error) {
      if (!applyServerErrors(error, setError, ["name"])) setFormError(t("createFailed"));
    }
  });

  return (
    <form onSubmit={onSubmit} noValidate className="flex flex-col gap-4">
      {formError ? (
        <div role="alert" className="rounded-md border border-danger-subtle bg-danger-subtle p-3">
          <p className="text-sm font-medium text-danger">{formError}</p>
        </div>
      ) : null}

      <Field
        label={t("nameLabel")}
        description={t("nameHint")}
        error={errors.name?.message}
        required
      >
        {(props) => <Input {...props} {...register("name")} autoComplete="organization" />}
      </Field>

      <SubmitButton pending={isSubmitting} pendingLabel={t("createPending")}>
        {t("createAction")}
      </SubmitButton>
    </form>
  );
}
