import { getTranslations } from "next-intl/server";

import { SignInForm } from "@/features/auth/sign-in-form";
import { Link } from "@/i18n/navigation";

export async function generateMetadata() {
  const t = await getTranslations("auth");
  return { title: t("signInTitle") };
}

export default async function SignInFormPage() {
  const t = await getTranslations("auth");

  return (
    <div>
      <h1 className="text-2xl font-semibold tracking-tight text-text">{t("signInTitle")}</h1>
      <p className="mt-1 text-sm text-text-muted">{t("signInSubtitle")}</p>
      <div className="mt-6">
        <SignInForm />
      </div>
      <div className="mt-6 flex flex-col gap-2 text-sm text-text-muted">
        <p>
          {t("noAccount")}{" "}
          <Link
            href="/sign-up"
            className="rounded-sm font-medium text-accent underline underline-offset-2"
          >
            {t("signUpAction")}
          </Link>
        </p>
        <p>
          <Link
            href="/reset-password"
            className="rounded-sm font-medium text-accent underline underline-offset-2"
          >
            {t("forgotPassword")}
          </Link>
        </p>
      </div>
    </div>
  );
}
