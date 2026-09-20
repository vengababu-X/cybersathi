import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { LogIn, ShieldCheck } from 'lucide-react'
import { useApp } from '@/context/AppContext'
import { FieldError, SectionTitle } from '@/components/ui/Bits'
import { loginSchema, type LoginForm } from '@/forms/validation'

const DEMO = [
  { email: 'admin@cybersathi.org', password: 'Admin@123', role: 'Admin' },
  { email: 'volunteer@cybersathi.org', password: 'Volunteer@123', role: 'Volunteer' },
]

export default function Login() {
  const { t } = useTranslation()
  const { signIn, user, signOut } = useApp()
  const navigate = useNavigate()
  const [failed, setFailed] = useState(false)

  const {
    register,
    handleSubmit,
    setValue,
    formState: { errors, isSubmitting },
  } = useForm<LoginForm>({
    resolver: zodResolver(loginSchema),
    defaultValues: { email: '', password: '' },
  })

  // Validation runs in zod; this only handles the server's answer.
  const onSubmit = handleSubmit(async (values) => {
    setFailed(false)
    try {
      await signIn(values.email, values.password)
      navigate('/workshops')
    } catch {
      setFailed(true)
    }
  })

  if (user) {
    return (
      <div className="mx-auto max-w-md">
        <div className="card p-8 text-center">
          <ShieldCheck size={36} className="mx-auto text-accent-600" aria-hidden />
          <p className="mt-3 text-sm text-slate-500">{t('auth.signedInAs')}</p>
          <p className="text-lg font-bold text-brand-800">{user.full_name}</p>
          <p className="text-sm text-slate-600">{user.email} · {user.role}</p>
          <button onClick={signOut} className="btn-ghost mt-5">{t('nav.logout')}</button>
        </div>
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-md space-y-5">
      <SectionTitle title={t('auth.signIn')} />

      {/* noValidate: zod owns the messages, so the browser must not pre-empt them. */}
      <form onSubmit={onSubmit} noValidate className="card space-y-4 p-6">
        <div>
          <label htmlFor="email" className="mb-1.5 block text-sm font-semibold text-slate-700">
            {t('auth.email')}
          </label>
          <input
            id="email"
            type="email"
            autoComplete="username"
            aria-invalid={errors.email ? true : undefined}
            aria-describedby={errors.email ? 'email-error' : undefined}
            {...register('email')}
            className="input"
          />
          <FieldError id="email-error" message={errors.email?.message} />
        </div>

        <div>
          <label htmlFor="password" className="mb-1.5 block text-sm font-semibold text-slate-700">
            {t('auth.password')}
          </label>
          <input
            id="password"
            type="password"
            autoComplete="current-password"
            aria-invalid={errors.password ? true : undefined}
            aria-describedby={errors.password ? 'password-error' : undefined}
            {...register('password')}
            className="input"
          />
          <FieldError id="password-error" message={errors.password?.message} />
        </div>

        {failed && (
          <p role="alert" className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-800">
            {t('auth.invalid')}
          </p>
        )}

        <button type="submit" disabled={isSubmitting} className="btn-primary w-full">
          <LogIn size={18} aria-hidden /> {isSubmitting ? t('auth.signingIn') : t('auth.signIn')}
        </button>
      </form>

      <div className="card p-5">
        <p className="mb-3 text-sm font-semibold text-slate-700">{t('auth.demoTitle')}</p>
        <div className="space-y-2">
          {DEMO.map((d) => (
            <button
              key={d.email}
              type="button"
              onClick={() => {
                setValue('email', d.email, { shouldValidate: true })
                setValue('password', d.password, { shouldValidate: true })
              }}
              className="flex w-full items-center justify-between rounded-lg border border-slate-200 px-3 py-2 text-left text-xs hover:border-brand-400"
            >
              <span className="font-mono text-slate-700">{d.email}</span>
              <span className="chip bg-brand-50 text-brand-700">{d.role}</span>
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
