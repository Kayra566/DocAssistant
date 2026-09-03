import { Component, type ReactNode } from "react";

interface Props {
  children: ReactNode;
}

interface State {
  error: Error | null;
}

/** Beklenmeyen render hatasında boş ekran yerine kurtarılabilir bir arayüz gösterir. */
export class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error) {
    console.error("Beklenmeyen arayüz hatası:", error);
  }

  render() {
    if (!this.state.error) return this.props.children;

    return (
      <div className="flex min-h-screen items-center justify-center p-6">
        <div className="w-full max-w-md space-y-4 rounded-xl border border-neutral-800 bg-neutral-900/60 p-6">
          <h1 className="text-xl font-semibold">Bir şeyler ters gitti</h1>
          <p className="text-sm text-neutral-400">
            Sayfa yüklenirken beklenmeyen bir hata oluştu.
          </p>
          <p className="break-words rounded-md border border-neutral-800 px-3 py-2 text-xs text-neutral-500">
            {this.state.error.message}
          </p>
          <div className="flex gap-2">
            <button
              onClick={() => this.setState({ error: null })}
              className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-500"
            >
              Tekrar dene
            </button>
            <a
              href="/dashboard"
              className="rounded-md border border-neutral-700 px-4 py-2 text-sm text-neutral-200 hover:bg-neutral-800"
            >
              Panele dön
            </a>
          </div>
        </div>
      </div>
    );
  }
}
