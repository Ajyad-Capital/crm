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
    navigationItems
      .filter((item) => item.desktopOnly)
      .forEach((item) => expect(mobileRoutes).not.toContain(item.route))
    expect(mobileRoutes).not.toContain('Calendar')
    expect(mobileRoutes).toContain('Contacts')
  })

  it('leaves hidden destinations out of the menus', () => {
    const routes = getNavigationItems().map((item) => item.route)
    expect(routes).not.toContain('Leads')
    expect(routes).not.toContain('Deals')
    expect(routes).not.toContain('Organizations')
    expect(routes).not.toContain('Dashboard')
    expect(routes).toContain('Contacts')
  })

  it('lists Transactions and Trades after Contacts', () => {
    const routes = getNavigationItems().map((item) => item.route)
    expect(routes).toEqual(
      expect.arrayContaining(['Contacts', 'Transactions', 'Trades']),
    )
    expect(routes.indexOf('Transactions')).toBeGreaterThan(
      routes.indexOf('Contacts'),
    )
    expect(routes.indexOf('Trades')).toBe(routes.indexOf('Transactions') + 1)
  })
})
