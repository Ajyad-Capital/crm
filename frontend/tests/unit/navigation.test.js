import { getNavigationItems, navigationItems } from '@/utils/navigation'

describe('navigationItems', () => {
  it('uses unique route names', () => {
    const routes = navigationItems.map((item) => item.route)
    expect(new Set(routes).size).toBe(routes.length)
  })

  it('omits desktop-only destinations on mobile', () => {
    const mobileRoutes = getNavigationItems({ mobile: true }).map(
      (item) => item.route,
    )
    expect(mobileRoutes).not.toContain('Dashboard')
    expect(mobileRoutes).not.toContain('Calendar')
    expect(mobileRoutes).toContain('Contacts')
  })

  it('leaves hidden destinations out of the menus', () => {
    const routes = getNavigationItems().map((item) => item.route)
    expect(routes).not.toContain('Leads')
    expect(routes).not.toContain('Deals')
    expect(routes).not.toContain('Organizations')
    expect(routes).toContain('Contacts')
  })
})
