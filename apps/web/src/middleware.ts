import createMiddleware from "next-intl/middleware";
import type { NextRequest } from "next/server";
import { NextResponse } from "next/server";

import { routing } from "./i18n/routing";

const handleLocale = createMiddleware(routing);

const ACCESS_COOKIE = "ai_workspace_access";

/** Path segments under a locale that require a session. */
const PROTECTED = ["workspace", "documents", "assistant", "usage", "settings"];

/**
 * Locale negotiation, then a cheap authentication redirect.
 *
 * The cookie check here only asks whether one is *present*. That is not proof of
 * anything — the real verification is `getServerUser` in the (app) layout, which
 * asks the API. This exists so a signed-out visitor is redirected before a page
 * is rendered and thrown away, not as the guard.
 */
export default function middleware(request: NextRequest) {
  const response = handleLocale(request);

  const segments = request.nextUrl.pathname.split("/").filter(Boolean);
  const [maybeLocale, section] = segments;
  const isLocale = (routing.locales as readonly string[]).includes(maybeLocale ?? "");
  if (!isLocale || !section || !PROTECTED.includes(section)) return response;

  if (!request.cookies.has(ACCESS_COOKIE)) {
    const signIn = new URL(`/${maybeLocale}/sign-in`, request.url);
    // Remember where they were going, so signing in does not dump them on a
    // dashboard they did not ask for.
    signIn.searchParams.set("next", request.nextUrl.pathname);
    return NextResponse.redirect(signIn);
  }

  return response;
}

export const config = {
  // Everything except Next's internals and files with an extension. Without the
  // exclusions the middleware would rewrite requests for the bundle itself.
  matcher: "/((?!api|_next|_vercel|.*\\..*).*)",
};
