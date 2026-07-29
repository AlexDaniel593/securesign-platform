import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

export function middleware(request: NextRequest) {
  const token = request.cookies.get('token')?.value
  const { pathname } = request.nextUrl

  const publicRoutes = ['/', '/login', '/register']
  const isPublicRoute = publicRoutes.some(route => 
    pathname === route || pathname.startsWith('/api/')
  )

  if (isPublicRoute) {
    return NextResponse.next()
  }

  if (!token) {
    const homeUrl = new URL('/', request.url)
    return NextResponse.redirect(homeUrl)
  }

  return NextResponse.next()
}

export const config = {
  matcher: [
    '/((?!_next/static|_next/image|favicon.ico|api/).*)',
  ],
}
