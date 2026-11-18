#!/usr/bin/env python3
# 修复：const app 不存在于 window，导致 V2/图库脚本提前退出
import sys, io

PATH = 'index.html'


def main():
    h = io.open(PATH, encoding='utf-8').read()
    if 'photoV2ConstFix' in h:
        print('already fixed, skip')
        return

    opened = 0
    a = "(function(){\n  if (!window.app) { console.log('photoV2: app not found'); return; }\n  var app = window.app;"
    if a in h:
        h = h.replace(a, "if (typeof app !== 'undefined') { // photoV2ConstFix", 1)
        opened += 1

    b = "(function(){\n  if (!window.app) return;\n  var app = window.app;"
    if b in h:
        h = h.replace(b, "if (typeof app !== 'undefined') { // photoV2ConstFix", 1)
        opened += 1

    if opened != 2:
        print('open anchors not both found, opened=', opened)
        sys.exit(1)

    closed = 0
    for _ in range(2):
        i = h.rfind("})();\n</script>")
        if i < 0:
            print('close anchor missing'); sys.exit(1)
        h = h[:i] + "}\n</script>" + h[i + len("})();\n</script>"):]
        closed += 1

    io.open(PATH, 'w', encoding='utf-8').write(h)
    print('fixed, opened', opened, 'closed', closed, 'len', len(h))


if __name__ == '__main__':
    main()
