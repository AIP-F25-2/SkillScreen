import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
    const hostname = request.headers.get('host');
    const { pathname } = request.nextUrl;

    // Check if the hostname is the portfolio subdomain
    // Matches: portfolio.skillscreen.dev, portfolio.localhost:3000, etc.
    if (hostname && (hostname.startsWith('portfolio.') || hostname === 'portfolio.skillscreen.dev')) {
        // If we're already at /portfolio, don't rewrite to avoid loops if not handled carefully,
        // but usually rewrite is internal.
        // We want to rewrite everything from root to /portfolio

        // Prevent rewriting static files or API routes if they are shared, 
        // but for a portfolio page we might want to be careful.
        // For now, let's rewrite non-static requests to /portfolio
        if (
            !pathname.startsWith('/_next') &&
            !pathname.startsWith('/api') &&
            !pathname.startsWith('/static') &&
            !pathname.includes('.') // exclude files with extensions (images, etc) usually
        ) {
            // Rewrite the URL to the portfolio path
            // This keeps the URL in the browser as portfolio.skillscreen.dev/foo
            // but serves the content from /portfolio/foo
            return NextResponse.rewrite(new URL(`/portfolio${pathname === '/' ? '' : pathname}`, request.url));
        }
    }

    return NextResponse.next();
}

export const config = {
    matcher: [
        /*
         * Match all request paths except for the ones starting with:
         * - api (API routes)
         * - _next/static (static files)
         * - _next/image (image optimization files)
         * - favicon.ico (favicon file)
         */
        '/((?!api|_next/static|_next/image|favicon.ico).*)',
    ],
};
