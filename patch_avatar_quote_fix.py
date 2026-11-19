#!/usr/bin/env python3
# 修复：1) 换头像识别不到"听宝宝的"等同意表达（加用户明确要换的前置 + 扩大同意词）
#       2) 发图回复通道泄露 [引用:序号] 标记（补 _extractAIQuote 清理）
#       3) 强化 prompt：同意必须写 [换头像] 标记
import io, sys

PATH = 'index.html'


def need(h, anchor, label):
    if anchor not in h:
        print('missing anchor:', label)
        sys.exit(1)


def main():
    h = io.open(PATH, encoding='utf-8').read()
    if 'avatarQuoteFix' in h:
        print('already fixed, skip')
        return

    old_judge = "var hasMarker = /(^|\\n)\\s*\\[换头像\\]\\s*($|\\n)/m.test(replyText);\n      var explicitAgree = /(现在就换|就换这个|好[，,。\\s]{0,10}换|同意[，,。\\s]{0,10}换)/.test(replyText) && !/(不换|别换|不想换|不愿意|再想想)/.test(replyText);\n      if (!hasMarker && !explicitAgree) return Promise.resolve(replyText);"
    need(h, old_judge, 'avatar judge')
    new_judge = ("var userWantSwitch = /(换.{0,4}头像|做.{0,4}头像|当.{0,4}头像|设为.{0,4}头像|用.{0,6}头像|换成这个|换这个|换了吧|换上)/.test(userText || '');\n"
                 "      var hasMarker = /(^|\\n)\\s*\\[换头像\\]\\s*($|\\n)/m.test(replyText);\n"
                 "      var refuse = /(不换|别换|不想换|不愿意|再想想|不喜欢|不好看|不合适)/.test(replyText);\n"
                 "      var agreeWords = /(现在就换|就换这个|好[，,。\\s]{0,10}换|同意[，,。\\s]{0,10}换|听你的|听宝宝的|好嘞|好啊|换成这个|这就换|这就换上|换上了|换好了)/.test(replyText);\n"
                 "      var explicitAgree = agreeWords && !refuse;\n"
                 "      if (!hasMarker && !(userWantSwitch && explicitAgree)) return Promise.resolve(replyText); // avatarQuoteFix")
    h = h.replace(old_judge, new_judge, 1)

    old_prompt_tail = "关于换头像：只有当用户这句话里明确表达了想让你把这张照片设为头像的意愿时，你才按自己的性格和审美决定是否同意；同意就在回复末尾单独一行写 [换头像]（不能只口头答应），不同意就自然拒绝或商量；如果用户只是分享照片、没有提换头像，就不要主动换。"
    need(h, old_prompt_tail, 'prompt tail')
    new_prompt_tail = "关于换头像：只有当用户这句话里明确表达了想让你把这张照片设为头像的意愿时，你才按自己的性格和审美决定是否同意。如果你同意，必须在回复的最后一行单独写 [换头像] 这个标记——系统只认这个标记来真正更换头像，你只说“好/听你的/听宝宝的”是不会执行的，等于没换；如果不同意就自然拒绝或商量，不要写标记。如果用户只是分享照片、没有提换头像，就不要主动换，也不要写标记。"
    h = h.replace(old_prompt_tail, new_prompt_tail, 1)

    old_clean = "}).then(function(cleaned) {\n        if (!cleaned || /请在设置中配置|请配置 API Key|网络波动中/.test(cleaned)) cleaned = '照片收到啦。刚刚我这边没能看清图片内容，你可以再跟我说说照片里是什么。';"
    need(h, old_clean, 'image reply clean')
    new_clean = "}).then(function(cleaned) {\n        if (app._extractAIQuote) cleaned = app._extractAIQuote(cleaned, role);\n        if (!cleaned || /请在设置中配置|请配置 API Key|网络波动中/.test(cleaned)) cleaned = '照片收到啦。刚刚我这边没能看清图片内容，你可以再跟我说说照片里是什么。';"
    h = h.replace(old_clean, new_clean, 1)

    io.open(PATH, 'w', encoding='utf-8').write(h)
    print('avatar + quote fixed, len', len(h))


if __name__ == '__main__':
    main()
