import { Menu, MoveRight } from 'lucide-react'
import { Link, NavLink, Outlet } from 'react-router-dom'
import { motion } from 'framer-motion'

const navItems = [
  { to: '/', label: 'Explorer' },
  { to: '/prioritization', label: 'Prioritization' },
  { to: '/map', label: 'Map' },
  { to: '/model', label: 'Model' },
]

function navClass(isActive: boolean) {
  return isActive
    ? 'rounded-full border border-accent/25 bg-accent/12 px-4 py-2 text-sm font-medium text-accent shadow-soft'
    : 'rounded-full px-4 py-2 text-sm font-medium text-charcoal/70 transition hover:bg-surface-2 hover:text-charcoal'
}

export function AppShell() {
  return (
    <div className="min-h-screen bg-canvas text-charcoal">
      <div className="absolute inset-x-0 top-0 -z-10 h-[36rem] bg-[radial-gradient(circle_at_top_left,_rgba(242,107,58,0.22),_transparent_34%),radial-gradient(circle_at_top_right,_rgba(236,196,144,0.28),_transparent_28%)]" />
      <header className="sticky top-0 z-30 border-b border-border/80 bg-canvas/85 backdrop-blur-xl">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4 lg:px-10">
          <Link to="/" className="flex items-center gap-3">
            <div className="grid h-11 w-11 place-items-center rounded-2xl border border-border bg-surface shadow-soft">
              <span className="font-display text-lg font-semibold text-accent">TB</span>
            </div>
            <div>
              <div className="text-xs uppercase tracking-[0.24em] text-charcoal/45">TB Futures</div>
              <div className="font-display text-xl text-charcoal">Global Prevention Lab</div>
            </div>
          </Link>
          <nav className="hidden items-center gap-2 lg:flex">
            {navItems.map((item) => (
              <NavLink key={item.to} to={item.to} end={item.to === '/'}>
                {({ isActive }) => <span className={navClass(isActive)}>{item.label}</span>}
              </NavLink>
            ))}
          </nav>
          <div className="flex items-center gap-3">
            <Link
              to="/prioritization"
              className="hidden rounded-full bg-accent px-5 py-3 text-sm font-semibold text-white shadow-[0_20px_40px_rgba(242,107,58,0.22)] transition hover:-translate-y-0.5 hover:bg-[#e55f2f] sm:inline-flex sm:items-center sm:gap-2"
            >
              Open Priority View
              <MoveRight className="h-4 w-4" />
            </Link>
            <button
              type="button"
              className="grid h-11 w-11 place-items-center rounded-full border border-border bg-surface text-charcoal lg:hidden"
              aria-label="Navigation menu"
            >
              <Menu className="h-5 w-5" />
            </button>
          </div>
        </div>
      </header>
      <main className="mx-auto flex max-w-7xl flex-col gap-10 px-6 py-8 lg:px-10 lg:py-10">
        <motion.div
          initial={{ opacity: 0, y: 14 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.42, ease: 'easeOut' }}
        >
          <Outlet />
        </motion.div>
      </main>
    </div>
  )
}
