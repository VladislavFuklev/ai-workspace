"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { z } from "zod";

import {
  Field,
  FormError,
  Input,
  SubmitButton,
  Textarea,
  applyServerErrors,
} from "@/components/form";
import { ApiError } from "@/lib/api";

/**
 * One schema, used for client validation and — once the endpoint exists — as the
 * shape sent to the API. Keeping them the same is the point: two schemas drift.
 */
const schema = z.object({
  name: z.string().min(3, "Give the workspace a name of at least 3 characters."),
  slug: z
    .string()
    .min(3, "At least 3 characters.")
    .regex(/^[a-z0-9-]+$/, "Lowercase letters, numbers and hyphens only."),
  description: z.string().max(280, "Keep it under 280 characters.").optional(),
});

type Values = z.infer<typeof schema>;
const FIELDS = ["name", "slug", "description"] as const;

/** Stand-in for the real endpoint. `taken` reproduces a server-side 422. */
async function submit(values: Values): Promise<void> {
  await new Promise((resolve) => setTimeout(resolve, 600));
  if (values.slug === "taken") {
    throw new ApiError({
      kind: "http",
      status: 422,
      message: "That workspace could not be created.",
      requestId: "req-demo-422",
      detail: [{ field: "slug", message: "This address is already in use." }],
    });
  }
  if (values.slug === "boom") {
    throw new ApiError({
      kind: "http",
      status: 503,
      message: "The service is temporarily unavailable.",
    });
  }
}

export function DemoForm() {
  const {
    register,
    handleSubmit,
    setError,
    formState: { errors, isSubmitting, isSubmitSuccessful },
  } = useForm<Values>({ resolver: zodResolver(schema), mode: "onBlur" });

  const onSubmit = handleSubmit(async (values) => {
    try {
      await submit(values);
    } catch (error) {
      // Field-level problems go back to their fields; anything else is form-level.
      if (!applyServerErrors(error, setError, FIELDS)) {
        setError("root", { message: error instanceof ApiError ? error.message : undefined });
      }
    }
  });

  return (
    <form onSubmit={onSubmit} noValidate className="flex max-w-md flex-col gap-4">
      <FormError
        error={
          errors.root ? new ApiError({ kind: "http", message: errors.root.message ?? "" }) : null
        }
      />

      <Field label="Workspace name" error={errors.name?.message} required>
        {(props) => <Input {...props} {...register("name")} placeholder="Acme Legal" />}
      </Field>

      <Field
        label="Address"
        description="Used in URLs. Try “taken” for a server-side field error, or “boom” for a form-level one."
        error={errors.slug?.message}
        required
      >
        {(props) => <Input {...props} {...register("slug")} placeholder="acme-legal" />}
      </Field>

      <Field label="Description" error={errors.description?.message}>
        {(props) => <Textarea {...props} {...register("description")} />}
      </Field>

      <div className="flex items-center gap-3">
        <SubmitButton pending={isSubmitting} pendingLabel="Creating">
          Create workspace
        </SubmitButton>
        {isSubmitSuccessful && !errors.root ? (
          <p role="status" className="text-sm text-success">
            Workspace created.
          </p>
        ) : null}
      </div>
    </form>
  );
}
