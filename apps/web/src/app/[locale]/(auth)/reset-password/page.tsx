import { getTranslations } from "next-intl/server";

import { ResetRequestForm } from "@/features/auth/reset-request-form";
import { Link } from "@/i18n/navigation";

export async function generateMetadata() {
  const t = await getTranslations("auth");
  return { title: t("resetTitle") };
}

export default async function ResetRequestFormPage() {
  const t = await getTranslations("auth");

  return (
    <div>
      <h1 className="text-2xl font-semibold tracking-tight text-text">{t("resetTitle")}</h1>
      <p className="mt-1 text-sm text-text-muted">{t("resetSubtitle")}</p>
      <div className="mt-6">
        <ResetRequestForm />
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
