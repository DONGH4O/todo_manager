# Todo Manager React Desktop UI

Next.js App Router implementation of the M6.5 React desktop interface.

```powershell
npm install
npm run dev
npm run build
```

Formal desktop data access is provided by `window.todoBridge`, injected by the QtWebEngine shell in `todo-gui --react`. Browser mode keeps a local preview fallback for design and layout work; release builds use the CLI JSON bridge.
