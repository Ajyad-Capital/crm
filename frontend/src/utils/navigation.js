import ContactsIcon from '@/components/Icons/ContactsIcon.vue'
import DealsIcon from '@/components/Icons/DealsIcon.vue'
import LeadsIcon from '@/components/Icons/LeadsIcon.vue'
import NoteIcon from '@/components/Icons/NoteIcon.vue'
import OrganizationsIcon from '@/components/Icons/OrganizationsIcon.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import TaskIcon from '@/components/Icons/TaskIcon.vue'
import LucideArrowLeftRight from '~icons/lucide/arrow-left-right'
import LucideLayoutDashboard from '~icons/lucide/layout-dashboard'
import LucideTrendingUp from '~icons/lucide/trending-up'
import router from '@/router'

export const navigationItems = [
  {
    label: 'Dashboard',
    icon: LucideLayoutDashboard,
    route: 'Dashboard',
    desktopOnly: true,
    hidden: true,
  },
  // hidden: routes stay registered (direct links work) but are left out of the menus
  { label: 'Leads', icon: LeadsIcon, route: 'Leads', hidden: true },
  { label: 'Deals', icon: DealsIcon, route: 'Deals', hidden: true },
  { label: 'Contacts', icon: ContactsIcon, route: 'Contacts' },
  {
    label: 'Organizations',
    icon: OrganizationsIcon,
    route: 'Organizations',
    hidden: true,
  },
  { label: 'Transactions', icon: LucideArrowLeftRight, route: 'Transactions' },
  { label: 'Trades', icon: LucideTrendingUp, route: 'Trades' },
  { label: 'Notes', icon: NoteIcon, route: 'Notes' },
  { label: 'Tasks', icon: TaskIcon, route: 'Tasks' },
  { label: 'Call Logs', icon: PhoneIcon, route: 'Call Logs' },
]

export function getNavigationItems({ mobile = false } = {}) {
  return navigationItems.filter(
    (item) =>
      !item.hidden &&
      router.hasRoute(item.route) &&
      (!mobile || !item.desktopOnly),
  )
}
