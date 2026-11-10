// Allow base64-encoded PNG images (data:) and inline CSS in HTML Publisher reports (dashboard.html),
// while keeping JavaScript execution disabled.
System.setProperty(
  'hudson.model.DirectoryBrowserSupport.CSP',
  "sandbox; default-src 'none'; img-src 'self' data:; style-src 'self' 'unsafe-inline';"
)

