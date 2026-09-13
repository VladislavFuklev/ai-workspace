import { getTranslations } from "next-intl/server";

import { SignUpForm } from "@/features/auth/sign-up-form";
import { Link } from "@/i18n/navigation";

export async function generateMetadata() {
  const t = await getTranslations("auth");
  return { title: t("signUpTitle") };
}

export default async function SignUpFormPage() {
  const t = await getTranslations("auth");

  return (
    <div>
      <h1 className="text-2xl font-semibold tracking-tight text-text">{t("signUpTitle")}</h1>
      <p className="mt-1 text-sm text-text-muted">{t("signUpSubtitle")}</p>
      <div className="mt-6">
        <SignUpForm />
      </div>
      <div className="mt-6 flex flex-col gap-2 text-sm text-text-muted">
        <p>
          {t("haveAccount")}{" "}
          <Link
            href="/sign-in"
            className="rounded-sm font-medium text-accent underline underline-offset-2"
          >
            {t("signInAction")}
          </Link>
        </p>
      </div>
    </div>
  );
}
