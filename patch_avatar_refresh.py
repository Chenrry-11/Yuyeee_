#!/usr/bin/env python3
# 换头像后刷新聊天顶部头像 + 消息流 + 同步旧 role.avatar 字段 + 成功提示
import io, sys

PATH = 'index.html'

OLD = """          app._ceWriteCharacter(roleId, function(c) { c.profile.avatar = avatarId; c.profile.avatarDesc = avatarDesc; });
          app.caRenderProfile && app.caRenderProfile();
          app.renderPocketChatList && app.renderPocketChatList();
          return cleanedText;"""

NEW = """          app._ceWriteCharacter(roleId, function(c) { c.profile.avatar = avatarId; c.profile.avatarDesc = avatarDesc; });
          if (role) role.avatar = avatarId;
          app.caRenderProfile && app.caRenderProfile();
          app.renderPocketChatList && app.renderPocketChatList();
          app.updateChatHeaderAvatar && app.updateChatHeaderAvatar(role);
          app.renderChatMessages && app.renderChatMessages();
          if (app._flash) app._flash('头像已更新');
          return cleanedText;"""


def main():
    h = io.open(PATH, encoding='utf-8').read()
    if 'avatarRefreshFix' in h:
        print('already fixed, skip')
        return
    if OLD not in h:
        print('anchor missing'); sys.exit(1)
    h = h.replace(OLD, NEW + ' // avatarRefreshFix', 1)
    io.open(PATH, 'w', encoding='utf-8').write(h)
    print('avatar refresh fixed, len', len(h))


if __name__ == '__main__':
    main()
