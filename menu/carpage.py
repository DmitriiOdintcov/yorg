'''This module provides the car page.'''
from direct.gui.DirectButton import DirectButton
from direct.gui.DirectGuiGlobals import DISABLED, NORMAL
from racing.game.engine.gui.page import Page, PageGui
from .netmsgs import NetMsgs


class CarPageGui(PageGui):
    '''This class defines the GUI of the car page.'''

    def __init__(self, mdt, menu):
        self.car = None
        self.current_cars = None
        self.track_path = None
        PageGui.__init__(self, mdt, menu)

    def build(self):
        menu_gui = self.menu.gui
        menu_args = self.menu.gui.menu_args
        self.track_path = 'tracks/track_' + self.menu.track
        if eng.server.is_active:
            eng.server.register_cb(self.process_srv)
            eng.server.car_mapping = {}
        elif eng.client.is_active:
            eng.client.register_cb(self.process_client)
        menu_data = [
            ('Kronos', self.on_car, ['kronos']),
            ('Themis', self.on_car, ['themis']),
            ('Diones', self.on_car, ['diones'])]
        self.widgets += [
            DirectButton(
                text=menu[0], scale=.2, pos=(0, 1, .4-i*.28),
                text_fg=(.75, .75, .75, 1),
                text_font=menu_gui.font, frameColor=menu_args.btn_color,
                command=menu[1], extraArgs=menu[2],
                frameSize=menu_args.btn_size,
                rolloverSound=loader.loadSfx('assets/sfx/menu_over.wav'),
                clickSound=loader.loadSfx('assets/sfx/menu_clicked.ogg'))
            for i, menu in enumerate(menu_data)]
        self.current_cars = {}
        PageGui.build(self)

    def __buttons(self, car):
        is_btn = lambda wdg: wdg.__class__ == DirectButton
        buttons = [wdg for wdg in self.widgets if is_btn(wdg)]
        return [btn for btn in buttons if wdg['extraArgs'] == [car]]

    def on_car(self, car):
        '''Called when the user clicks on a car.'''
        if eng.server.is_active:
            eng.log_mgr.log('car selected: ' + car)
            eng.server.send([NetMsgs.car_selection, car])
            for btn in self.__buttons(car):
                btn['state'] = DISABLED
                btn.setAlphaScale(.25)
            if self in self.current_cars:
                curr_car = self.current_cars[self]
                eng.log_mgr.log('car deselected: ' + curr_car)
                eng.server.send([NetMsgs.car_deselection, curr_car])
                for btn in self.__buttons(curr_car):
                    btn['state'] = NORMAL
                    btn.setAlphaScale(1)
            self.current_cars[self] = car
            eng.server.car_mapping['self'] = car
            self.evaluate_starting()
        elif eng.client.is_active:
            eng.log_mgr.log('car request: ' + car)
            eng.client.send([NetMsgs.car_request, car])
        else:
            game.fsm.demand('Loading', self.track_path, car)

    def evaluate_starting(self):
        '''Evaluate if we should start.'''
        connections = eng.server.connections + [self]
        if all(conn in self.current_cars for conn in connections):
            packet = [NetMsgs.start_race]
            packet += [len(self.current_cars)]

            def process(k):
                '''Processes a car.'''
                return 'server' if k == self else k.getAddress().getIpString()
            for k, val in self.current_cars.items():
                packet += [process(k), val]
            eng.server.send(packet)
            eng.log_mgr.log('start race: ' + str(packet))
            curr_car = self.current_cars[self]
            game.fsm.demand('Loading', self.track_path, curr_car, packet[2:])

    def process_srv(self, data_lst, sender):
        '''Processes a message server-side.'''
        if data_lst[0] == NetMsgs.car_request:
            car = data_lst[1]
            eng.log_mgr.log('car requested: ' + car)
            btn = self.__buttons(car)[0]
            if btn['state'] == DISABLED:
                eng.server.send([NetMsgs.car_deny], sender)
                eng.log_mgr.log('car already selected: ' + car)
            elif btn['state'] == NORMAL:
                eng.log_mgr.log('car selected: ' + car)
                self.current_cars[sender] = car
                btn['state'] = DISABLED
                eng.server.send([NetMsgs.car_confirm, car], sender)
                eng.server.send([NetMsgs.car_selection, car])
                eng.server.car_mapping[sender] = car
                self.evaluate_starting()

    def process_client(self, data_lst, sender):
        '''Processes a message client-side.'''
        if data_lst[0] == NetMsgs.car_confirm:
            self.car = car = data_lst[1]
            eng.log_mgr.log('car confirmed: ' + car)
            btn = self.buttons(car)[0]
            btn['state'] = DISABLED
            btn.setAlphaScale(.25)
        if data_lst[0] == NetMsgs.car_deny:
            eng.log_mgr.log('car denied')
        if data_lst[0] == NetMsgs.car_selection:
            car = data_lst[1]
            eng.log_mgr.log('car selection: ' + car)
            btn = self.__buttons(car)[0]
            btn['state'] = DISABLED
            btn.setAlphaScale(.25)
        if data_lst[0] == NetMsgs.car_deselection:
            car = data_lst[1]
            eng.log_mgr.log('car deselection: ' + car)
            btn = self.__buttons(car)[0]
            btn['state'] = NORMAL
            btn.setAlphaScale(1)
        if data_lst[0] == NetMsgs.start_race:
            eng.log_mgr.log('start_race: ' + str(data_lst))
            game.fsm.demand('Loading', self.track_path, self.car, data_lst[2:])


class CarPage(Page):
    '''This class models a page.'''
    gui_cls = CarPageGui