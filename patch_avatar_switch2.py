#!/usr/bin/env python3
# 二次修复：模型口头同意但漏写内部标记时，识别明确同意；拒绝仍不执行
import io, sys

PATH = 'index.html'


def main():
    h = io.open(PATH, encoding='utf-8').read()
    if 'avatarSwitchFix2' in h:
        print('already fixed, skip')
        return
    old1 = "var prompt = '用户刚发来一张照片。图片内容（由视觉识别得到）：' + desc + '。请结合你的性格、审美、你们的关系和当前聊天，像真的看到照片一样自然回应，可以问照片里的内容；想回表情包就单独一行写 [表情包]档名（如 [表情包]开心）。是否把这张照片设为头像必须由你自己判断：同意就在回复末尾单独一行写 [换头像]；不同意就自然拒绝或商量，不要写。'; // avatarSwitchFix"
    new1 = "var prompt = '用户刚发来一张照片。图片内容（由视觉识别得到）：' + desc + '。请结合你的性格、审美、你们的关系和当前聊天，像真的看到照片一样自然回应，可以问照片里的内容；想回表情包就单独一行写 [表情包]档名（如 [表情包]开心）。是否把这张照片设为头像必须由你自己判断：同意就必须在回复末尾单独一行写 [换头像]，不能只口头答应；不同意就自然拒绝或商量，不要写。'; // avatarSwitchFix2"
    old2 = "      if (!/(^|\\n)\\s*\\[换头像\\]\\s*($|\\n)/m.test(replyText)) return Promise.resolve(replyText);\n      var cleanedText = replyText.replace(/(^|\\n)\\s*\\[换头像\\]\\s*($|\\n)/g, '\\n').trim();"
    new2 = "      var hasMarker = /(^|\\n)\\s*\\[换头像\\]\\s*($|\\n)/m.test(replyText);\n      var explicitAgree = /(现在就换|就换这个|好[，,。\\s]{0,10}换|同意[，,。\\s]{0,10}换)/.test(replyText) && !/(不换|别换|不想换|不愿意|再想想)/.test(replyText);\n      if (!hasMarker && !explicitAgree) return Promise.resolve(replyText);\n      var cleanedText = replyText.replace(/(^|\\n)\\s*\\[换头像\\]\\s*($|\\n)/g, '\\n').trim();"
    if old1 not in h or old2 not in h:
        print('anchors missing'); sys.exit(1)
    h = h.replace(old1, new1, 1).replace(old2, new2, 1)
    io.open(PATH, 'w', encoding='utf-8').write(h)
    print('avatar switch fix2 applied, len', len(h))


if __name__ == '__main__':
    main()
