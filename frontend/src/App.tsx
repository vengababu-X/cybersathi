import { Component, Suspense, lazy } from 'react'
import type { ReactNode } from 'react'
import { Route, Routes } from 'react-router-dom'
import Layout from '@/components/layout/Layout'
import { Spinner, ErrorState } from '@/components/ui/Bits'

const Home = lazy(() => import('@/pages/Home'))
const ScamAnalyzer = lazy(() => import('@/pages/ScamAnalyzer'))
const UrlChecker = lazy(() => import('@/pages/UrlChecker'))
const QrUpiSafety = lazy(() => import('@/pages/QrUpiSafety'))
const KnowledgeBase = lazy(() => import('@/pages/KnowledgeBase'))
const ArticleDetail = lazy(() => import('@/pages/ArticleDetail'))
const Assistant = lazy(() => import('@/pages/Assistant'))
const Assessment = lazy(() => import('@/pages/Assessment'))
const Dashboard = lazy(() => import('@/pages/Dashboard'))
const Workshops = lazy(() => import('@/pages/Workshops'))
const Login = lazy(() => import('@/pages/Login'))
const About = lazy(() => import('@/pages/About'))
const Admin = lazy(() => import('@/pages/Admin'))
const NotFound = lazy(() => import('@/pages/NotFound'))

/** A render error in one page must not blank the whole app. */
class ErrorBoundary extends Component<{ children: ReactNode }, { hasError: boolean }> {
  state = { hasError: false }
  static getDerivedStateFromError() { return { hasError: true } }
  render() {
    if (this.state.hasError) {
      return <ErrorState onRetry={() => { this.setState({ hasError: false }); window.location.reload() }} />
    }
    return this.props.children
  }
}

export default function App() {
  return (
    <ErrorBoundary>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Suspense fallback={<Spinner />}><Home /></Suspense>} />
          <Route path="analyzer" element={<Suspense fallback={<Spinner />}><ScamAnalyzer /></Suspense>} />
          <Route path="url" element={<Suspense fallback={<Spinner />}><UrlChecker /></Suspense>} />
          <Route path="qr" element={<Suspense fallback={<Spinner />}><QrUpiSafety /></Suspense>} />
          <Route path="learn" element={<Suspense fallback={<Spinner />}><KnowledgeBase /></Suspense>} />
          <Route path="learn/:slug" element={<Suspense fallback={<Spinner />}><ArticleDetail /></Suspense>} />
          <Route path="ask" element={<Suspense fallback={<Spinner />}><Assistant /></Suspense>} />
          <Route path="assessment" element={<Suspense fallback={<Spinner />}><Assessment /></Suspense>} />
          <Route path="dashboard" element={<Suspense fallback={<Spinner />}><Dashboard /></Suspense>} />
          <Route path="workshops" element={<Suspense fallback={<Spinner />}><Workshops /></Suspense>} />
          <Route path="login" element={<Suspense fallback={<Spinner />}><Login /></Suspense>} />
          <Route path="about" element={<Suspense fallback={<Spinner />}><About /></Suspense>} />
          <Route path="admin" element={<Suspense fallback={<Spinner />}><Admin /></Suspense>} />
          <Route path="*" element={<Suspense fallback={<Spinner />}><NotFound /></Suspense>} />
        </Route>
      </Routes>
    </ErrorBoundary>
  )
}
