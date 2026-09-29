# 3. Client-Side Rendering with Observable Plot and D3

## Status
accepted

Report entries must be interactive, responsive to viewport resizing, and capable of fast theme switching. We chose to transform data on the server into a normalized JSON Visualization Payload and render graphics directly in the browser using Observable Plot (and D3 for pie/donut charts) rather than generating static chart images on the server. This provides crisp vector rendering, interactive tooltips, responsive grid reflow, and keeps server load minimal.

### Considered Options
- **Server-side Image Generation (matplotlib / seaborn)**: Rejected due to high server memory overhead, lack of interactivity (tooltips, hover highlights), and poor responsiveness across varying screen sizes.
- **Legacy Chart Libraries (C3.js)**: Previously used in earlier versions, but migrated to Observable Plot to leverage a modern declarative grammar of graphics.

### Consequences
- Browser clients require JavaScript enabled to render visualizations.
- Offline PDF generation or print exports require a headless browser render pipeline rather than direct image serving.
