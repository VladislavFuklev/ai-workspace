import createMiddleware from "next-intl/middleware";
import type { NextRequest } from "next/server";
import { NextResponse } from "next/server";

import { ORGANIZATION_COOKIE } from "./features/organizations/cookie";
import { RESERVED_SEGMENTS } from "./features/organizations/reserved";
import { routing } from "./i18n/routing";

const handleLocale = createMiddleware(routing);

const ACCESS_COOKIE = "ai_workspace_access";

/** Sections inside an organisation: `/{locale}/{organization}/{section}`. */
const SECTIONS = ["workspace", "documents", "assistant", "usage", "settings"];

/** Signed-in pages that are not inside an organisation. */
const ORGANIZATION_FREE = ["enter", "organizations"];

const RESERVED: readonly string[] = RESERVED_SEGMENTS;

/** A year: it is a convenience, and forgetting it is the only cost of expiry. */
const REMEMBER_FOR_SECONDS = 60 * 60 * 24 * 365;

/**
 * Locale negotiation, then a cheap authentication redirect, then remembering
 * which organisation this browser last looked at.
 *
 * The cookie check here only asks whether one is *present*. That is not proof of
 * anything — the real verification is `getServerUser` in the (app) layout, which
 * asks the API. This exists so a signed-out visitor is redirected before a page
 * is rendered and thrown away, not as the guard.
 *
 * The organisation cookie is written here because the middleware already sees
 * every path and can set a cookie on the response, which a Server Component
 * cannot. It is only a memory of the last choice; the URL is what decides what
 * is shown, and the API decides who may see it.
 */
export default function middleware(request: NextRequest) {
  const response = handleLocale(request);

  const segments = request.nextUrl.pathname.split("/").filter(Boolean);
  const [maybeLocale, first, second] = segments;
  if (!(routing.locales as readonly string[]).includes(maybeLocale ?? "")) return response;

  const organizationFree = first !== undefined && ORGANIZATION_FREE.includes(first);
  const insideOrganization = second !== undefined && SECTIONS.includes(second);
  // `/{locale}/{organization}` on its own is the organisation's front door.
  // Redirected here rather than by a page, because a page would have to render
  // the shell first and the redirect would arrive mid-stream.
  const bareOrganization = first !== undefined && second === undefined && !RESERVED.includes(first);
  if (!organizationFree && !insideOrganization && !bareOrganization) return response;

  if (!request.cookies.has(ACCESS_COOKIE)) {
    const signIn = new URL(`/${maybeLocale}/sign-in`, request.url);
    // Remember where they were going, so signing in does not dump them on a
    // dashboard they did not ask for.
    signIn.searchParams.set("next", request.nextUrl.pathname);
    return NextResponse.redirect(signIn);
  }

  if (bareOrganization) {
    return NextResponse.redirect(new URL(`/${maybeLocale}/${first}/workspace`, request.url));
  }

  if (insideOrganization && first) {
    response.cookies.set(ORGANIZATION_COOKIE, first, {
      path: "/",
      sameSite: "lax",
      maxAge: REMEMBER_FOR_SECONDS,
      // Readable by script on purpose: it holds no authority, and marking it
      // HttpOnly would imply otherwise.
      httpOnly: false,
    });
  }

  return response;
}

export const config = {
  // Everything except Next's internals and files with an extension. Without the
  // exclusions the middleware would rewrite requests for the bundle itself.
  matcher: "/((?!api|_next|_vercel|.*\\..*).*)",
};
