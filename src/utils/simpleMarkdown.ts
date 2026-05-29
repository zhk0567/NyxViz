/** Minimal markdown → HTML string (headings, lists, paragraphs). */
export function simpleMarkdownToHtml(text: string): string {
  const lines = text.split(/\r?\n/);
  const out: string[] = [];
  let inList = false;

  const closeList = () => {
    if (inList) {
      out.push('</ul>');
      inList = false;
    }
  };

  for (const line of lines) {
    if (line.startsWith('## ')) {
      closeList();
      out.push(`<h3>${renderInline(line.slice(3))}</h3>`);
    } else if (line.startsWith('### ')) {
      closeList();
      out.push(`<h4>${renderInline(line.slice(4))}</h4>`);
    } else if (line.startsWith('- ')) {
      if (!inList) {
        out.push('<ul>');
        inList = true;
      }
      out.push(`<li>${renderInline(line.slice(2))}</li>`);
    } else if (line.startsWith('![')) {
      continue;
    } else if (line.trim() === '---') {
      closeList();
      out.push('<hr />');
    } else if (line.trim() === '') {
      closeList();
    } else if (line.trim()) {
      closeList();
      out.push(`<p>${renderInline(line)}</p>`);
    }
  }
  closeList();
  return out.join('\n');
}

function escapeHtml(s: string): string {
  return s
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function renderInline(s: string): string {
  // Escape first, then re-introduce a tiny subset of markdown inline syntax.
  // Supported: **strong**, `code`
  let x = escapeHtml(s);

  // Inline code first to avoid interpreting ** inside code spans.
  x = x.replace(/`([^`]+)`/g, (_m, code) => `<code>${code}</code>`);
  x = x.replace(/\*\*([^*]+)\*\*/g, (_m, strong) => `<strong>${strong}</strong>`);
  return x;
}
