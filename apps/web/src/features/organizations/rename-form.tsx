"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useTranslations } from "next-intl";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { Field, Input, SubmitButton, applyServerErrors } from "@/components/form";

import { renameOrganization } from "./api";
import { MAX_ORGANIZATION_NAME, type Organization } from "./schemas";

/**
 * Changes the display name. The address stays as it is, which is said on the
 * form rather than discovered afterwards by someone whose links broke.
 */
export function RenameOrganizationForm({ organization }: { organization: Organization }) {
  const t = useTranslations("organizations");
  // Next's own router: nothing here navigates, and `refresh` re-renders the
  // server components that hold the name.
  const router = useRouter();
  const [saved, setSaved] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const schema = z.object({
    name: z.string().trim().min(1, t("nameRequired")).max(MAX_ORGANIZATION_NAME, t("nameTooLong")),
  });

  const {
    register,
    handleSubmit,
    setError,
    formState: { errors, isSubmitting },
  } = useForm<z.infer<typeof schema>>({
    resolver: zodResolver(schema),
    defaultValues: { name: organization.name },
  });

  const onSubmit = handleSubmit(async (values) => {
    setFormError(null);
    setSaved(false);
    try {
      await renameOrganization(organization.slug, values.name);
      router.refresh();
      setSaved(true);
    } catch (error) {
      if (!applyServerErrors(error, setError, ["name"])) setFormError(t("renameFailed"));
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
        description={t("addressFixed", { slug: organization.slug })}
        error={errors.name?.message}
        required
      >
        {(props) => <Input {...props} {...register("name")} autoComplete="organization" />}
      </Field>

      <div className="flex items-center gap-3">
        <SubmitButton pending={isSubmitting} pendingLabel={t("renamePending")}>
          {t("renameAction")}
        </SubmitButton>
        {/* Announced, not just coloured: a silent save looks like a failed one. */}
        <p role="status" className="text-sm text-text-muted">
          {saved ? t("renameSaved") : ""}
        </p>
      </div>
    </form>
  );
}
