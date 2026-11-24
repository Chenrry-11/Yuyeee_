#!/usr/bin/env python3
# AI 识别用户发图中的 [换头像] 指令，并真正把图片设为角色头像
import io, sys

PATH = 'index.html'


def main():
    h = io.open(PATH, encoding='utf-8').read()
    if 'avatarSwitchFix' in h:
        print('already fixed, skip')
        return

    old_prompt = "var prompt = '用户刚发来一张照片。图片内容（由视觉识别得到）：' + desc + '。请结合你们的关系和人设，像真的看到照片一样自然回应，可以问照片里的内容；想回表情包就单独一行写 [表情包]档名（如 [表情包]开心）。';"
    new_prompt = "var prompt = '用户刚发来一张照片。图片内容（由视觉识别得到）：' + desc + '。请结合你的性格、审美、你们的关系和当前聊天，像真的看到照片一样自然回应，可以问照片里的内容；想回表情包就单独一行写 [表情包]档名（如 [表情包]开心）。是否把这张照片设为头像必须由你自己判断：同意就在回复末尾单独一行写 [换头像]；不同意就自然拒绝或商量，不要写。'; // avatarSwitchFix"
    if old_prompt not in h:
        print('vision prompt anchor missing'); sys.exit(1)
    h = h.replace(old_prompt, new_prompt, 1)

    old_fallback = "var fallbackText = '用户刚刚给你发来了一张照片。请结合你们的关系和当前聊天，自然回应收到照片这件事；不要假装看到了照片里的具体细节。';"
    new_fallback = "var fallbackText = '用户刚刚给你发来了一张照片，但你这边没有成功看清图片内容。请自然回应，并说明你没看清，不能假装看到具体内容，也不能同意换头像。'; // avatarSwitchFix"
    if old_fallback not in h:
        print('fallback anchor missing'); sys.exit(1)
    h = h.replace(old_fallback, new_fallback, 1)

    helper_anchor = "sendChatImage: function(imageId, dataUrl) {"
    helper = helper_anchor + r"""
    var _applyAvatarSwitch = function(replyText) {
      if (!imageMsg.content.desc) return Promise.resolve(replyText);
      if (!/(^|\n)\s*\[换头像\]\s*($|\n)/m.test(replyText)) return Promise.resolve(replyText);
      var cleanedText = replyText.replace(/(^|\n)\s*\[换头像\]\s*($|\n)/g, '\n').trim();
      var avatarDesc = imageMsg.content.desc.length > 300 ? imageMsg.content.desc.substring(0, 300) : imageMsg.content.desc;
      return app.imageDB.get(imageId).then(function(data) {
        var avatarId = 'img_avatar_' + Date.now() + '_' + Math.random().toString(36).slice(2, 8);
        return app.imageDB.save(avatarId, data).then(function() {
          app._ceWriteCharacter(roleId, function(c) { c.profile.avatar = avatarId; c.profile.avatarDesc = avatarDesc; });
          app.caRenderProfile && app.caRenderProfile();
          app.renderPocketChatList && app.renderPocketChatList();
          return cleanedText;
        });
      }).catch(function() { return cleanedText; });
    };
"""
    h = h.replace(helper_anchor, helper, 1)

    old_chain = "visionPromise.then(function(reply) { return reply ? String(reply) : app.fetchAI(fallbackText, role); }).then(function(reply) {\n        app.removeThinkingBubble();\n        var cleaned = String(reply || '').trim();"
    new_chain = "visionPromise.then(function(reply) { return reply ? String(reply) : app.fetchAI(fallbackText, role); }).then(function(reply) {\n        app.removeThinkingBubble();\n        return _applyAvatarSwitch(String(reply || '').trim());\n      }).then(function(cleaned) {"
    if old_chain not in h:
        print('chain anchor missing'); sys.exit(1)
    h = h.replace(old_chain, new_chain, 1)

    io.open(PATH, 'w', encoding='utf-8').write(h)
    print('avatar switch fixed, len', len(h))


if __name__ == '__main__':
    main()
