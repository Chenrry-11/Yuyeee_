#!/usr/bin/env python3
# 修复：navigateTo 白名单缺少图库页与画风页，导致跳回主页
import sys, io

PATH = 'index.html'

ANCHOR = "            case 'sticker-manage-view': tv = $('sticker-manage-view'); app.currentView = 'sticker-manage'; app.renderStickerManage(); break;"
ADD = ANCHOR + (
    "\n            case 'art-style-config-view': tv = $('art-style-config-view'); app.currentView = 'art-style-config'; if (app.fillArtStyle) app.fillArtStyle(); break;"
    "\n            case 'character-gallery-view': tv = $('character-gallery-view'); app.currentView = 'character-gallery'; if (app._galRender) app._galRender(); break;")


def main():
    h = io.open(PATH, encoding='utf-8').read()
    if "case 'character-gallery-view':" in h:
        print('already registered, skip')
        return
    if ANCHOR not in h:
        print('nav anchor missing'); sys.exit(1)
    h = h.replace(ANCHOR, ADD, 1)
    io.open(PATH, 'w', encoding='utf-8').write(h)
    print('nav registered, len', len(h))


if __name__ == '__main__':
    main()
