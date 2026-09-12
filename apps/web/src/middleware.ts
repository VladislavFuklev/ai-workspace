import createMiddleware from "next-intl/middleware";

import { routing } from "./i18n/routing";

/**
 * Negotiates the locale for a request with no prefix: the cookie first, then
 * `Accept-Language`, then the default.
 */
export default createMiddleware(routing);

export const config = {
  // Everything except Next's internals and files with an extension. Without the
  // exclusions the middleware would rewrite requests for the bundle itself.
  matcher: "/((?!api|_next|_vercel|.*\\..*).*)",
};
