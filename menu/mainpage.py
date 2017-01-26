from direct.gui.DirectButton import DirectButton
from direct.gui.DirectGuiGlobals import DISABLED, NORMAL
from yyagl.engine.gui.mainpage import MainPage, MainPageGui
from yyagl.engine.gui.page import PageGui
from .singleplayerpage import SingleplayerPage
from .multiplayerpage import MultiplayerPage
from .optionpage import OptionPage
from .creditpage import CreditPage
from direct.gui.OnscreenImage import OnscreenImage


class YorgMainPageGui(MainPageGui):

    def build_page(self):
        menu_data = [
            ('Single Player', _('Single Player'),
             lambda: self.menu.logic.push_page(SingleplayerPage(self.menu))),
            ('Multiplayer', _('Multiplayer'),
             lambda: self.menu.logic.push_page(MultiplayerPage(self.menu))),
            ('Options', _('Options'),
             lambda: self.menu.logic.push_page(OptionPage(self.menu))),
            ('Credits', _('Credits'),
             lambda: self.menu.logic.push_page(CreditPage(self.menu))),
            ('Quit', _('Quit'),
             lambda: game.fsm.demand('Exit'))]
        menu_gui = self.menu.gui
        self.widgets += [
            DirectButton(text='', pos=(0, 1, .4-i*.28), command=menu[2],
                         **menu_gui.btn_args)
            for i, menu in enumerate(menu_data)]
        for i, wdg in enumerate(self.widgets):
            PageGui.transl_text(wdg, menu_data[i][0], menu_data[i][1])
        self.widgets[-4]['state'] = NORMAL if game.options['development']['multiplayer'] else DISABLED
        self.widgets += [OnscreenImage(
            'assets/images/gui/yorg_title.png',
            scale=(.8, 1, .8 * (380.0 / 772)), parent=base.a2dTopRight,
            pos=(-.8, 1, -.4))]
        self.widgets[-1].setTransparency(True)
        MainPageGui.build_page(self)


class YorgMainPage(MainPage):
    gui_cls = YorgMainPageGui
