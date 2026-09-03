/**
 * Sentry ve PostHog yalnızca ilgili env değişkeni tanımlıysa yüklenir.
 * Dinamik import sayesinde yapılandırılmamış kurulumlarda paket bundle'a girmez.
 */

const consent = () =>
  localStorage.getItem("docassistant-cookie-consent") === "accepted";

export async function initObservability(): Promise<void> {
  const sentryDsn = import.meta.env.VITE_SENTRY_DSN;
  if (sentryDsn) {
    const Sentry = await import("@sentry/react");
    Sentry.init({
      dsn: sentryDsn,
      environment: import.meta.env.MODE,
      tracesSampleRate: Number(import.meta.env.VITE_SENTRY_SAMPLE_RATE ?? 0.1),
      sendDefaultPii: false,
    });
  }

  const posthogKey = import.meta.env.VITE_POSTHOG_KEY;
  if (posthogKey && consent()) {
    const posthog = (await import("posthog-js")).default;
    posthog.init(posthogKey, {
      api_host: import.meta.env.VITE_POSTHOG_HOST ?? "https://eu.i.posthog.com",
      person_profiles: "identified_only",
      autocapture: false,
    });
  }
}

export async function captureEvent(
  name: string,
  properties?: Record<string, unknown>,
): Promise<void> {
  if (!import.meta.env.VITE_POSTHOG_KEY || !consent()) return;
  const posthog = (await import("posthog-js")).default;
  posthog.capture(name, properties);
}
