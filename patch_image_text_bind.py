#!/usr/bin/env python3
# 图+话强绑定：选图进输入框预览 -> 打字 -> 图+话作为一条消息发出（气泡分开显示）
# 换头像时 AI 同时拿到"这张图 + 这句话"，准确判断、按性格决定
import io, sys

PATH = 'index.html'

DRAFT_HTML = '''<div id="chat-image-draft" style="display:none;padding:8px 12px 0;">
  <div style="position:relative;display:inline-block;">
    <img id="chat-image-draft-thumb" style="max-height:90px;max-width:90px;border-radius:10px;display:block;object-fit:cover;">
    <button type="button" onclick="app.clearChatImageDraft()" style="position:absolute;top:-6px;right:-6px;width:20px;height:20px;border-radius:50%;background:rgba(0,0,0,.55);color:#fff;border:none;font-size:13px;line-height:1;cursor:pointer;">×</button>
  </div>
</div>
'''

DRAFT_SCRIPT = '''
<script>
if (typeof app !== 'undefined') { // imageTextBind
  app._chatImageDraft = null;
  app.setChatImageDraft = function(imageId, dataUrl) {
    app._chatImageDraft = { imageId: imageId, dataUrl: dataUrl };
    var thumb = document.getElementById('chat-image-draft-thumb');
    var bar = document.getElementById('chat-image-draft');
    if (thumb) thumb.src = dataUrl;
    if (bar) bar.style.display = 'block';
    var inp = document.getElementById('chat-detail-input');
    if (inp) inp.focus();
  };
  app.clearChatImageDraft = function() {
    app._chatImageDraft = null;
    var bar = document.getElementById('chat-image-draft');
    if (bar) bar.style.display = 'none';
  };
}
</script>
'''


def need(h, anchor, label):
    if anchor not in h:
        print('missing anchor:', label)
        sys.exit(1)


def main():
    h = io.open(PATH, encoding='utf-8').read()
    if 'imageTextBind' in h:
        print('already fixed, skip')
        return

    a1 = '<div class="text-input-row" id="dynamic-input-row">'
    need(h, a1, 'input row')
    h = h.replace(a1, DRAFT_HTML + a1, 1)

    a2 = 'app.sendChatImage(imageId, b64);'
    need(h, a2, 'sendChatImage call')
    h = h.replace(a2, 'app.setChatImageDraft(imageId, b64);', 1)

    a3 = "var input = $('chat-detail-input');\n    var text = input.value.trim();\n    if (!text) return;"
    need(h, a3, 'sendMessage head')
    new3 = ("var input = $('chat-detail-input');\n    var text = input.value.trim();\n"
            "    var _imgDraft = app._chatImageDraft;\n"
            "    if (_imgDraft && _imgDraft.imageId) {\n"
            "        app.clearChatImageDraft();\n"
            "        input.value = '';\n"
            "        app.sendChatImage(_imgDraft.imageId, _imgDraft.dataUrl, text);\n"
            "        return;\n"
            "    }\n"
            "    if (!text) return;")
    h = h.replace(a3, new3, 1)

    a4 = 'sendChatImage: function(imageId, dataUrl) {'
    need(h, a4, 'sendChatImage signature')
    h = h.replace(a4, 'sendChatImage: function(imageId, dataUrl, userText) {', 1)

    a5 = "var imageMsg = { sender: 'user', msgType: 'image', content: { imageId: imageId, text: '' }, ts: Date.now() };"
    need(h, a5, 'imageMsg content')
    h = h.replace(a5, "var imageMsg = { sender: 'user', msgType: 'image', content: { imageId: imageId, text: userText || '' }, ts: Date.now() };", 1)

    old_prompt = "var prompt = '用户刚发来一张照片。图片内容（由视觉识别得到）：' + desc + '。请结合你的性格、审美、你们的关系和当前聊天，像真的看到照片一样自然回应，可以问照片里的内容；想回表情包就单独一行写 [表情包]档名（如 [表情包]开心）。是否把这张照片设为头像必须由你自己判断：同意就必须在回复末尾单独一行写 [换头像]，不能只口头答应；不同意就自然拒绝或商量，不要写。'; // avatarSwitchFix2"
    need(h, old_prompt, 'prompt')
    new_prompt = "var prompt = '用户刚发来一张照片' + (userText ? '，并附上一句话：「' + userText + '」' : '') + '。图片内容（由视觉识别得到）：' + desc + '。请结合你的性格、审美、你们的关系和当前聊天，像真的看到照片一样自然回应用户的话和这张照片，可以问照片里的内容；想回表情包就单独一行写 [表情包]档名（如 [表情包]开心）。关于换头像：只有当用户这句话里明确表达了想让你把这张照片设为头像的意愿时，你才按自己的性格和审美决定是否同意；同意就在回复末尾单独一行写 [换头像]（不能只口头答应），不同意就自然拒绝或商量；如果用户只是分享照片、没有提换头像，就不要主动换。'; // imageTextBindPrompt"
    h = h.replace(old_prompt, new_prompt, 1)

    a6 = "html += app._wrapMessageWithMenu(imageHtml, m.ts, 'image', m.ts);\n        break;"
    need(h, a6, 'image render')
    new6 = ("html += app._wrapMessageWithMenu(imageHtml, m.ts, 'image', m.ts);\n"
            "        if (imageContent.text) {\n"
            "            var imgTextHtml = '<div class=\"msg-bubble\" style=\"padding:7px 12px;background:' + (isUserGroup ? 'var(--bubble-me)' : 'var(--bubble-char)') + ';border-radius:12px;font-size:13.5px;line-height:1.45;color:var(--text-main);word-wrap:break-word;max-width:85%;border:1px solid var(--border-light);margin-top:4px;\">' + app.richText(imageContent.text) + '</div>';\n"
            "            html += app._wrapMessageWithMenu(imgTextHtml, m.ts, 'text', m.ts);\n"
            "        }\n"
            "        break;")
    h = h.replace(a6, new6, 1)

    h = h.replace('</body>', DRAFT_SCRIPT + '\n</body>', 1)

    io.open(PATH, 'w', encoding='utf-8').write(h)
    print('image+text bind fixed, len', len(h))


if __name__ == '__main__':
    main()
