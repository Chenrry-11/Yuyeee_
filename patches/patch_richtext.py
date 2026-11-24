#!/usr/bin/env python3
# 富文本（**放大** *斜体* ~~删除线~~）+ 分隔符（/// 兼容 --- —— — ===）
# 覆盖：Pocket Chat（renderTextMessage）、瞬息 + 剧本（tracesParseInline 共用）
import io, sys

PATH = 'index.html'

RICH_SCRIPT = '''
<script>
if (typeof app !== 'undefined') { // richTextFix
  app.richText = function(text) {
    if (!text) return '';
    var s = esc(text);
    s = s.replace(/([（\\(][^）\\)]*[）\\)])/g, '<span class="chat-bracket-styled">$1</span>');
    s = s.replace(/\\*\\*([^*\\n]+)\\*\\*/g, '<strong style="font-weight:700;font-size:1.15em;">$1</strong>');
    s = s.replace(/\\*([^*\\n]+)\\*/g, '<em style="font-style:italic;">$1</em>');
    s = s.replace(/~~([^~\\n]+)~~/g, '<del style="text-decoration:line-through;opacity:.6;">$1</del>');
    return s;
  };
}
</script>
'''


def main():
    h = io.open(PATH, encoding='utf-8').read()
    if 'richTextFix' in h:
        print('already fixed, skip')
        return

    old_traces = "tracesParseInline(text) { if (!text) return ''; return esc(text).replace(/([（\\(][^）\\)]*[）\\)])/g, '<span class=\"chat-bracket-styled\">$1</span>'); },"
    new_traces = "tracesParseInline(text) { return app.richText(text); },"
    if old_traces not in h:
        print('tracesParseInline anchor missing'); sys.exit(1)
    h = h.replace(old_traces, new_traces, 1)

    old_pocket = "' + esc(bubbleContent) + app._extraHtml(m, false) + '"
    new_pocket = "' + app.richText(bubbleContent) + app._extraHtml(m, false) + '"
    if old_pocket not in h:
        print('renderTextMessage anchor missing'); sys.exit(1)
    h = h.replace(old_pocket, new_pocket, 1)

    old_sep = "var segments = text.split(/\\n\\s*---\\s*\\n/)"
    new_sep = "var segments = text.split(/\\n\\s*(?:---|—+|–+|===|\\/\\/\\/)\\s*\\n/)"
    if old_sep not in h:
        print('separator anchor missing'); sys.exit(1)
    h = h.replace(old_sep, new_sep, 1)

    h = h.replace('</body>', RICH_SCRIPT + '\n</body>', 1)

    io.open(PATH, 'w', encoding='utf-8').write(h)
    print('rich text + separator fixed, len', len(h))


if __name__ == '__main__':
    main()
