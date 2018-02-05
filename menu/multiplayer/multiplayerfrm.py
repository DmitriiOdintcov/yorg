from sleekxmpp.jid import JID
from yyagl.gameobject import GameObject
from yyagl.engine.logic import VersionChecker
from .usersfrm import UsersFrm
from .matchfrm import MatchFrm
from .messagefrm import MessageFrm
from .friend_dlg import FriendDialog
from .invite_dlg import InviteDialog
from .exit_dlg import ExitDialog


class MultiplayerFrm(GameObject):

    def __init__(self, menu_args):
        GameObject.__init__(self)
        self.dialog = None
        self.ver_check = VersionChecker()
        self.labels = []
        self.invited_users = []
        self.menu_args = menu_args
        self.users_frm = UsersFrm(menu_args)
        self.users_frm.attach(self.on_invite)
        self.users_frm.attach(self.on_add_chat)
        self.users_frm.attach(self.on_add_groupchat)
        self.msg_frm = MessageFrm(menu_args)
        self.msg_frm.attach(self.on_msg_focus)
        self.msg_frm.attach(self.on_close_all_chats)
        self.match_frm = None
        #self.match_frm.hide()
        self.msg_frm.hide()
        self.eng.xmpp.attach(self.on_users)
        self.eng.xmpp.attach(self.on_user_connected)
        self.eng.xmpp.attach(self.on_user_disconnected)
        self.eng.xmpp.attach(self.on_user_subscribe)
        self.eng.xmpp.attach(self.on_presence_available)
        self.eng.xmpp.attach(self.on_presence_available_room)
        self.eng.xmpp.attach(self.on_presence_unavailable_room)
        self.eng.xmpp.attach(self.on_presence_unavailable)
        self.eng.xmpp.attach(self.on_msg)
        self.eng.xmpp.attach(self.on_groupchat_msg)
        self.eng.xmpp.attach(self.on_invite_chat)
        self.eng.xmpp.attach(self.on_declined)
        self.eng.xmpp.attach(self.on_cancel_invite)

    def create_match_frm(self, room):
        self.match_frm = MatchFrm(self.menu_args)
        self.match_frm.attach(self.on_start)
        self.match_frm.show(room)

    def show(self):
        self.users_frm.show()
        #self.match_frm.show()
        self.msg_frm.show()

    def hide(self):
        self.users_frm.hide()
        #self.match_frm.hide()
        self.msg_frm.hide()

    def on_user_subscribe(self, user):
        if self.eng.xmpp.is_friend(user): return
        self.dialog = FriendDialog(self.menu_args, user)
        self.dialog.attach(self.on_friend_answer)

    def on_friend_answer(self, user, val):
        self.dialog.detach(self.on_friend_answer)
        self.dialog = self.dialog.destroy()
        self.eng.xmpp.client.send_presence_subscription(
            pto=user,
            pfrom=self.eng.xmpp.client.boundjid.full,
            ptype='subscribed' if val else 'unsubscribed')
        self.on_users()

    def on_invite(self, usr):
        if not self.match_frm:
            self.create_match_frm('')
        self.match_frm.on_invite(usr)

    def on_users(self): self.users_frm.on_users()

    def on_user_connected(self, user): self.users_frm.on_users()

    def on_user_disconnected(self, user): self.users_frm.on_users()

    def on_presence_available(self, user): self.users_frm.on_users()

    def on_presence_available_room(self, msg):
        self.match_frm.on_presence_available_room(msg)
        self.msg_frm.on_presence_available_room(msg)

    def on_presence_unavailable_room(self, msg):
        if self.match_frm:
            self.match_frm.on_presence_unavailable_room(msg)
        self.msg_frm.on_presence_unavailable_room(msg)
        if str(msg['muc']['nick']) == self.users_frm.in_match_room:
            self.exit_dlg = ExitDialog(self.menu_args, msg)
            self.exit_dlg.attach(self.on_exit_dlg)

    def on_exit_dlg(self):
        self.exit_dlg.destroy()
        self.notify('on_srv_quitted')
        self.on_room_back()

    def on_presence_unavailable(self, user): self.users_frm.on_users()

    def on_start(self): self.users_frm.room_name = None

    def on_room_back(self):
        if self.users_frm.room_name:  # i am the server:
            invited = self.users_frm.invited_users
            users = self.match_frm.users_names
            pending_users = [usr[2:] for usr in users if usr.startswith('? ')]
            for usr in pending_users:
                self.eng.xmpp.client.send_message(
                    mfrom=self.eng.xmpp.client.boundjid.full,
                    mto=usr,
                    mtype='chat',
                    msubject='cancel_invite',
                    mbody='cancel_invite')
        if self.msg_frm.curr_match_room:  # if we've accepted the invitation
            self.eng.xmpp.client.plugin['xep_0045'].leaveMUC(
                self.msg_frm.curr_match_room, self.eng.xmpp.client.boundjid.bare)
            self.match_frm.destroy()
            self.match_frm = None
            self.msg_frm.on_room_back()
        self.users_frm.invited_users = []
        self.users_frm.in_match_room = None
        self.users_frm.room_name = None
        self.on_users()

    def on_msg(self, msg):
        self.users_frm.set_size(False)
        self.msg_frm.show()
        self.msg_frm.on_msg(msg)

    def on_close_all_chats(self):
        self.users_frm.set_size(True)
        self.msg_frm.hide()

    def on_groupchat_msg(self, msg): self.msg_frm.on_groupchat_msg(msg)

    def on_invite_chat(self, msg):
        self.invite_dlg = InviteDialog(self.menu_args, msg)
        self.invite_dlg.attach(self.on_invite_answer)

    def on_invite_answer(self, msg, val):
        self.invite_dlg.detach(self.on_invite_answer)
        self.invite_dlg = self.invite_dlg.destroy()
        if val:
            self.users_frm.in_match_room = msg['from'].bare
            self.users_frm.on_users()
            self.msg_frm.add_groupchat(str(msg['body']), str(msg['from'].bare))
            self.eng.xmpp.client.plugin['xep_0045'].joinMUC(
                msg['body'], self.eng.xmpp.client.boundjid.bare)
            room = msg['body']
            nick = self.eng.xmpp.client.boundjid.bare
            self.create_match_frm(room)
            self.notify('on_create_room', room, nick)
        else:
            self.eng.xmpp.client.send_message(
                mfrom=self.eng.xmpp.client.boundjid.full,
                mto=str(msg['from'].bare),
                msubject='declined',
                mbody=str(msg['body']))

    def on_declined(self, msg):
        self.users_frm.on_declined(msg)
        self.match_frm.on_declined(msg)

    def on_cancel_invite(self):
        self.invite_dlg.detach(self.on_invite_answer)
        self.invite_dlg = self.invite_dlg.destroy()

    def on_add_chat(self, usr):
        self.users_frm.set_size(False)
        self.msg_frm.show()
        self.msg_frm.add_chat(usr)

    def on_add_groupchat(self, room, usr):
        self.users_frm.set_size(False)
        self.msg_frm.show()
        self.msg_frm.add_groupchat(room, usr)
        self.match_frm.room = room
        self.notify('on_create_room', room, usr)

    def on_msg_focus(self, val): self.notify('on_msg_focus', val)

    def destroy(self):
        self.frm = self.frm.destroy()
        GameObject.destroy(self)
