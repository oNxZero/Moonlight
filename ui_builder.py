import gi
import os
import tempfile
import time
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib, Gdk

MOON_SVG = """<?xml version="1.0" encoding="UTF-8"?>
<svg width="64px" height="64px" viewBox="0 0 24 24" version="1.1" xmlns="http://www.w3.org/2000/svg">
    <path d="M12.0000002,2.0000002 C12.2855146,2.0000002 12.5649479,2.02237834 12.8373396,2.06546059 C8.97157672,2.67699175 6.00000016,6.02897621 6.00000016,10 C6.00000016,14.4182782 9.58172216,18.0000002 14.0000002,18.0000002 C17.9710241,18.0000002 21.3230086,15.0284236 21.9345398,11.1626607 C21.9776221,11.4350524 22.0000002,11.7144857 22.0000002,12.0000002 C22.0000002,17.5228477 17.5228477,22.0000002 12.0000002,22.0000002 C6.47715266,22.0000002 2.00000016,17.5228477 2.00000016,12.0000002 C2.00000016,6.47715266 6.47715266,2.0000002 12.0000002,2.0000002 Z" fill="#cad3f5" stroke="none"></path>
</svg>
"""

class MainWindow(Adw.ApplicationWindow):
    def __init__(self, app, backend_toggle, backend_config, backend_suspend, listener, initial_config):
        super().__init__(application=app, title="Moonlight")

        self.set_default_size(740, 600)
        self.set_resizable(False)

        self.backend_toggle = backend_toggle
        self.backend_config = backend_config
        self.backend_suspend = backend_suspend
        self.listener = listener
        self.cfg = initial_config

        self.last_focus_time = 0
        self.master_active = False
        self.is_binding = False
        self.last_bind_time = 0

        self.saved_target_code = self.cfg.get('target_btn', -1)
        self.saved_target_name = listener.get_nice_name(self.saved_target_code)

        self.connect("notify::is-active", self.on_window_focus_change)

        self.mouse_blocker = Gtk.GestureClick()
        self.mouse_blocker.set_button(0)
        self.mouse_blocker.set_propagation_phase(Gtk.PropagationPhase.CAPTURE)
        self.mouse_blocker.connect("pressed", self.on_mouse_block_press)
        self.mouse_blocker.connect("released", self.on_mouse_block_release)
        self.add_controller(self.mouse_blocker)

        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_content(root)

        header = Adw.HeaderBar()
        header.set_show_end_title_buttons(False)
        header.set_show_start_title_buttons(False)
        lbl_title = Gtk.Label(label="Moonlight")
        lbl_title.set_css_classes(["title-label"])
        header.set_title_widget(lbl_title)

        box_win_ctrl = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        btn_min = Gtk.Button(icon_name="window-minimize-symbolic")
        btn_min.set_css_classes(["win-ctrl"])
        btn_min.set_focusable(False)
        btn_min.connect("clicked", lambda x: self.minimize())

        btn_close = Gtk.Button(icon_name="window-close-symbolic")
        btn_close.set_css_classes(["win-ctrl", "close"])
        btn_close.set_focusable(False)
        btn_close.connect("clicked", lambda x: app.quit())

        box_win_ctrl.append(btn_min)
        box_win_ctrl.append(btn_close)
        header.pack_end(box_win_ctrl)
        root.append(header)

        hero = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=24)
        hero.set_css_classes(["card", "hero-card"])

        self.tmp_icon = tempfile.NamedTemporaryFile(suffix=".svg", delete=False)
        self.tmp_icon.write(MOON_SVG.encode('utf-8'))
        self.tmp_icon.close()
        self.icon_status = Gtk.Image.new_from_file(self.tmp_icon.name)
        self.icon_status.set_pixel_size(64)
        self.icon_status.set_css_classes(["icon-pulse"])
        hero.append(self.icon_status)

        vbox_st = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        vbox_st.set_valign(Gtk.Align.CENTER)
        self.lbl_status = Gtk.Label(label="DISABLED", xalign=0)
        self.lbl_status.set_css_classes(["h1"])
        self.lbl_sub = Gtk.Label(label="Waiting for input...", xalign=0)
        self.lbl_sub.set_css_classes(["dim"])
        vbox_st.append(self.lbl_status)
        vbox_st.append(self.lbl_sub)
        hero.append(vbox_st)

        self.box_master = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        self.box_master.set_valign(Gtk.Align.CENTER)
        self.box_master.set_halign(Gtk.Align.END)
        self.box_master.set_hexpand(True)
        self.box_master.set_css_classes(["segmented-box", "master-box", "pos-left"])
        self.box_master.set_homogeneous(True)
        self.btn_master_off = Gtk.ToggleButton(label="OFF")
        self.btn_master_off.set_css_classes(["segment-btn"])
        self.btn_master_off.set_active(True)
        self.btn_master_off.set_focusable(False)
        self.btn_master_off.connect("toggled", self.on_master_toggled)
        self.btn_master_on = Gtk.ToggleButton(label="ON")
        self.btn_master_on.set_css_classes(["segment-btn"])
        self.btn_master_on.set_group(self.btn_master_off)
        self.btn_master_on.set_focusable(False)
        self.box_master.append(self.btn_master_off)
        self.box_master.append(self.btn_master_on)
        self.sw_shield = Gtk.GestureClick()
        self.sw_shield.set_propagation_phase(Gtk.PropagationPhase.CAPTURE)
        self.sw_shield.connect("pressed", self.on_switch_click_attempt)
        self.box_master.add_controller(self.sw_shield)
        hero.append(self.box_master)
        root.append(hero)

        hbox_middle = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        hbox_middle.set_homogeneous(True)

        card_act = self.create_card("ACTIVATION")
        row_mode = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        lbl_appmode = Gtk.Label(label="Target Mode", xalign=0, hexpand=True)
        self.seg_mode = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        self.seg_mode.set_css_classes(["segmented-box", "pos-left"])
        self.seg_mode.set_homogeneous(True)
        self.btn_mode_mouse = Gtk.ToggleButton(label="Mouse")
        self.btn_mode_mouse.set_css_classes(["segment-btn"])

        if self.cfg.get('mode') == 'keyboard':
            self.btn_mode_mouse.set_active(False)
            self.seg_mode.add_css_class("pos-right")
            self.seg_mode.remove_css_class("pos-left")
        else:
            self.btn_mode_mouse.set_active(True)
            self.seg_mode.add_css_class("pos-left")
            self.seg_mode.remove_css_class("pos-right")

        self.btn_mode_mouse.set_focusable(False)
        self.btn_mode_mouse.connect("toggled", self.on_app_mode_changed)
        self.btn_mode_kb = Gtk.ToggleButton(label="Keyboard")
        self.btn_mode_kb.set_css_classes(["segment-btn"])
        self.btn_mode_kb.set_group(self.btn_mode_mouse)
        self.btn_mode_kb.set_focusable(False)
        self.seg_mode.append(self.btn_mode_mouse)
        self.seg_mode.append(self.btn_mode_kb)
        row_mode.append(lbl_appmode)
        row_mode.append(self.seg_mode)
        card_act.append(row_mode)
        card_act.append(self.create_sep())

        row_trig = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        lbl_trig = Gtk.Label(label="Trigger Type", xalign=0, hexpand=True)
        self.seg_trig = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        self.seg_trig.set_css_classes(["segmented-box", "pos-left"])
        self.seg_trig.set_homogeneous(True)
        self.btn_trig_tog = Gtk.ToggleButton(label="Toggle")
        self.btn_trig_tog.set_css_classes(["segment-btn"])

        if self.cfg.get('trigger_mode') == 'hold':
            self.btn_trig_tog.set_active(False)
            self.seg_trig.add_css_class("pos-right")
            self.seg_trig.remove_css_class("pos-left")
        else:
            self.btn_trig_tog.set_active(True)
            self.seg_trig.add_css_class("pos-left")
            self.seg_trig.remove_css_class("pos-right")

        self.btn_trig_tog.set_focusable(False)
        self.btn_trig_tog.connect("toggled", self.on_trig_mode_changed)
        self.btn_trig_hold = Gtk.ToggleButton(label="Hold")
        self.btn_trig_hold.set_css_classes(["segment-btn"])
        self.btn_trig_hold.set_group(self.btn_trig_tog)
        self.btn_trig_hold.set_focusable(False)
        self.seg_trig.append(self.btn_trig_tog)
        self.seg_trig.append(self.btn_trig_hold)
        row_trig.append(lbl_trig)
        row_trig.append(self.seg_trig)
        card_act.append(row_trig)
        card_act.append(self.create_sep())

        self.row_bind_left = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        self.lbl_bind_left = Gtk.Label(label="Left Click Trigger", xalign=0, hexpand=True)

        t_left_name = listener.get_nice_name(self.cfg.get('trigger_left', 64))
        self.btn_bind_left = Gtk.Button(label=t_left_name)

        self.btn_bind_left.set_css_classes(["trigger-btn"])
        self.btn_bind_left.set_focusable(False)
        self.btn_bind_left.connect("clicked", lambda x: self.on_bind_click("trigger_left"))
        self.row_bind_left.append(self.lbl_bind_left)
        self.row_bind_left.append(self.btn_bind_left)
        card_act.append(self.row_bind_left)

        self.row_bind_right = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        lbl_bind_right = Gtk.Label(label="Right Click Trigger", xalign=0, hexpand=True)

        t_right_name = listener.get_nice_name(self.cfg.get('trigger_right', 65))
        self.btn_bind_right = Gtk.Button(label=t_right_name)

        self.btn_bind_right.set_css_classes(["trigger-btn"])
        self.btn_bind_right.set_focusable(False)
        self.btn_bind_right.connect("clicked", lambda x: self.on_bind_click("trigger_right"))
        self.row_bind_right.append(lbl_bind_right)
        self.row_bind_right.append(self.btn_bind_right)
        card_act.append(self.row_bind_right)

        hbox_middle.append(card_act)

        self.card_assist = self.create_card("ASSIST")
        row_wtap = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        lbl_wtap = Gtk.Label(label="W-Tap", xalign=0, hexpand=True)
        sw_wtap = Gtk.Switch()
        sw_wtap.set_active(self.cfg.get('assist_wtap', False))
        sw_wtap.set_valign(Gtk.Align.CENTER)
        sw_wtap.connect("notify::active", lambda w, p: self.backend_config({'assist_wtap': w.get_active()}))
        row_wtap.append(lbl_wtap)
        row_wtap.append(sw_wtap)
        self.card_assist.append(row_wtap)

        self.add_slider(self.card_assist, "W-Tap Chance %", 0, 100, self.cfg.get('assist_wtap_chance', 5.0), 1, lambda v: self.backend_config({'assist_wtap_chance': v}))

        self.card_assist.append(self.create_sep())

        row_bh = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        lbl_bh = Gtk.Label(label="Blockhit", xalign=0, hexpand=True)
        sw_bh = Gtk.Switch()
        sw_bh.set_active(self.cfg.get('assist_blockhit', False))
        sw_bh.set_valign(Gtk.Align.CENTER)
        sw_bh.connect("notify::active", lambda w, p: self.backend_config({'assist_blockhit': w.get_active()}))
        row_bh.append(lbl_bh)
        row_bh.append(sw_bh)
        self.card_assist.append(row_bh)

        self.add_slider(self.card_assist, "Blockhit Chance %", 0, 100, self.cfg.get('assist_blockhit_chance', 10.0), 1, lambda v: self.backend_config({'assist_blockhit_chance': v}))

        hbox_middle.append(self.card_assist)
        root.append(hbox_middle)

        self.card_conf = self.create_card("CONFIGURATION")
        self.row_target = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        lbl_target = Gtk.Label(label="Target Key", xalign=0, hexpand=True)
        self.btn_target = Gtk.Button(label="Select...")
        self.btn_target.set_css_classes(["trigger-btn"])
        self.btn_target.set_focusable(False)
        self.btn_target.connect("clicked", lambda x: self.on_bind_click("target"))
        self.row_target.append(lbl_target)
        self.row_target.append(self.btn_target)
        self.card_conf.append(self.row_target)

        self.box_cps_left, self.lbl_cps_left = self.add_slider(self.card_conf, "Left Click CPS", 1.0, 20.0, self.cfg.get('cps_left', 12.0), 0.5, lambda v: self.backend_config({'cps_left': v}))
        self.sep_cps_right = self.create_sep()
        self.card_conf.append(self.sep_cps_right)
        self.box_cps_right, _ = self.add_slider(self.card_conf, "Right Click CPS", 1.0, 20.0, self.cfg.get('cps_right', 12.0), 0.5, lambda v: self.backend_config({'cps_right': v}))
        self.sep_jitter = self.create_sep()
        self.card_conf.append(self.sep_jitter)
        self.box_jitter, _ = self.add_slider(self.card_conf, "Left Click Jitter", 0.0, 10.0, self.cfg.get('jitter', 2.0), 0.5, lambda v: self.backend_config({'jitter': v}))
        self.card_conf.append(self.create_sep())

        row_rand = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        lbl_rand = Gtk.Label(label="Humanization", xalign=0, hexpand=True)
        self.seg_rand = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        self.seg_rand.set_css_classes(["segmented-box", "pos-left"])
        self.seg_rand.set_homogeneous(True)
        self.btn_legit = Gtk.ToggleButton(label="Legit")
        self.btn_legit.set_css_classes(["segment-btn"])

        if self.cfg.get('rand') == 2:
            self.btn_legit.set_active(False)
            self.seg_rand.add_css_class("pos-right")
            self.seg_rand.remove_css_class("pos-left")
        else:
            self.btn_legit.set_active(True)
            self.seg_rand.add_css_class("pos-left")
            self.seg_rand.remove_css_class("pos-right")

        self.btn_legit.set_focusable(False)
        self.btn_legit.connect("toggled", self.on_human_toggled)
        self.btn_blatant = Gtk.ToggleButton(label="Blatant")
        self.btn_blatant.set_css_classes(["segment-btn"])
        self.btn_blatant.set_group(self.btn_legit)
        self.btn_blatant.set_focusable(False)
        self.seg_rand.append(self.btn_legit)
        self.seg_rand.append(self.btn_blatant)
        row_rand.append(lbl_rand)
        row_rand.append(self.seg_rand)
        self.card_conf.append(row_rand)

        self.card_conf.append(self.create_sep())
        row_hide = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        lbl_hide = Gtk.Label(label="Hide GUI", xalign=0, hexpand=True)

        h_key_name = listener.get_nice_name(self.cfg.get('hide_key', 54))
        self.btn_hide = Gtk.Button(label=h_key_name)

        self.btn_hide.set_css_classes(["trigger-btn"])
        self.btn_hide.set_focusable(False)
        self.btn_hide.connect("clicked", lambda x: self.on_bind_click("hide"))
        row_hide.append(lbl_hide)
        row_hide.append(self.btn_hide)
        self.card_conf.append(row_hide)

        self.card_conf.set_margin_bottom(8)

        root.append(self.card_conf)

        self.refresh_ui_mode()

    def create_card(self, title):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_css_classes(["card"])
        lbl = Gtk.Label(label=title, xalign=0)
        lbl.set_css_classes(["h2"])
        box.append(lbl)
        return box

    def create_sep(self):
        sep = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        sep.set_css_classes(["white-sep"])
        sep.set_margin_top(0)
        sep.set_margin_bottom(0)
        return sep

    def add_slider(self, parent, title, min_v, max_v, def_v, step, callback):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
        head = Gtk.Box()
        t = Gtk.Label(label=title, xalign=0, hexpand=True)
        v = Gtk.Label(label=f"{def_v:.1f}")
        v.set_css_classes(["accent"])
        head.append(t)
        head.append(v)
        box.append(head)
        adj = Gtk.Adjustment(value=def_v, lower=min_v, upper=max_v, step_increment=step, page_increment=step)
        scale = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL, adjustment=adj)
        scale.set_digits(1)
        scale.set_round_digits(1)
        def _cb(s):
            raw = s.get_value()
            snapped = round(raw / step) * step
            if abs(raw - snapped) > 0.01: s.set_value(snapped)
            v.set_label(f"{snapped:.1f}")
            callback(snapped)
        scale.connect("value-changed", _cb)
        box.append(scale)
        parent.append(box)
        return box, t

    def on_window_focus_change(self, win, _):
        is_focused = win.get_property("is-active")
        if is_focused: self.last_focus_time = time.time()
        self.listener.set_paused(is_focused)
        self.backend_suspend(is_focused)

    def on_switch_click_attempt(self, gesture, n_press, x, y):
        if time.time() - self.last_focus_time < 0.2:
            gesture.set_state(Gtk.EventSequenceState.CLAIMED)

    def on_mouse_block_press(self, gesture, n_press, x, y):
        btn = gesture.get_current_button()
        if btn > 3:
            gesture.set_state(Gtk.EventSequenceState.CLAIMED)
            return True

    def on_mouse_block_release(self, gesture, n_press, x, y):
        btn = gesture.get_current_button()
        if btn > 3:
            gesture.set_state(Gtk.EventSequenceState.CLAIMED)
            return True

    def on_master_toggled(self, btn):
        is_on = not self.btn_master_off.get_active()
        self.update_master_visuals(is_on)
        if is_on: self.backend_toggle(True, 'left')
        else:
            self.backend_toggle(False, 'left')
            self.backend_toggle(False, 'right')

    def update_master_visuals(self, active):
        if active:
            self.box_master.add_css_class("pos-right")
            self.box_master.remove_css_class("pos-left")
            self.lbl_status.set_label("ENABLED")
            self.lbl_status.add_css_class("status-active")
            self.icon_status.add_css_class("active")
            self.lbl_sub.set_label("Injecting input stream...")
            if not self.btn_master_on.get_active(): self.btn_master_on.set_active(True)
        else:
            self.box_master.add_css_class("pos-left")
            self.box_master.remove_css_class("pos-right")
            self.lbl_status.set_label("DISABLED")
            self.lbl_status.remove_css_class("status-active")
            self.icon_status.remove_css_class("active")
            self.lbl_sub.set_label("Waiting for input...")
            if not self.btn_master_off.get_active(): self.btn_master_off.set_active(True)

    def set_active_visuals(self, active_left, active_right):
        self.btn_master_off.handler_block_by_func(self.on_master_toggled)
        self.update_master_visuals(active_left or active_right)
        self.btn_master_off.handler_unblock_by_func(self.on_master_toggled)

    def on_app_mode_changed(self, btn):
        mode = "mouse" if self.btn_mode_mouse.get_active() else "keyboard"
        self.backend_config({'mode': mode})
        if mode == "mouse":
            self.seg_mode.add_css_class("pos-left")
            self.seg_mode.remove_css_class("pos-right")
        else:
            self.seg_mode.add_css_class("pos-right")
            self.seg_mode.remove_css_class("pos-left")
            if self.saved_target_code is not None:
                self.backend_config({'target_btn': self.saved_target_code})
            else:
                self.backend_config({'target_btn': -1})
        self.listener.set_app_mode(mode)
        self.refresh_ui_mode()

    def refresh_ui_mode(self):
        is_mouse = self.btn_mode_mouse.get_active()
        self.card_assist.set_visible(is_mouse)

        if is_mouse:
            self.row_bind_right.set_visible(True)
            self.box_cps_right.set_visible(True)
            self.sep_cps_right.set_visible(True)
            self.box_jitter.set_visible(True)
            self.sep_jitter.set_visible(True)
            self.row_target.set_visible(False)
            self.lbl_bind_left.set_label("Left Click Trigger")
            self.lbl_cps_left.set_label("Left Click CPS")
        else:
            self.row_target.set_visible(True)
            self.row_bind_right.set_visible(False)
            self.box_cps_right.set_visible(False)
            self.sep_cps_right.set_visible(False)
            self.box_jitter.set_visible(False)
            self.sep_jitter.set_visible(False)
            self.lbl_bind_left.set_label("Trigger Key")
            self.lbl_cps_left.set_label("Key Tap CPS")
            self.btn_target.set_label(self.saved_target_name)

    def on_trig_mode_changed(self, btn):
        if self.btn_trig_tog.get_active():
            self.seg_trig.add_css_class("pos-left")
            self.seg_trig.remove_css_class("pos-right")
            self.listener.set_trigger_mode("toggle")
            self.backend_config({'trigger_mode': 'toggle'})
        else:
            self.seg_trig.add_css_class("pos-right")
            self.seg_trig.remove_css_class("pos-left")
            self.listener.set_trigger_mode("hold")
            self.backend_config({'trigger_mode': 'hold'})

    def on_human_toggled(self, btn):
        if self.btn_legit.get_active():
            self.seg_rand.add_css_class("pos-left")
            self.seg_rand.remove_css_class("pos-right")
            self.backend_config({'rand': 1})
        else:
            self.seg_rand.add_css_class("pos-right")
            self.seg_rand.remove_css_class("pos-left")
            self.backend_config({'rand': 2})

    def on_bind_click(self, mode):
        if self.is_binding: return
        if time.time() - self.last_bind_time < 0.5: return
        self.is_binding = True
        btn = None
        if mode == "trigger_left": btn = self.btn_bind_left
        elif mode == "trigger_right": btn = self.btn_bind_right
        elif mode == "target": btn = self.btn_target
        elif mode == "hide": btn = self.btn_hide
        if btn: btn.set_label("Press Button / Key")
        self.listener.start_rebind(mode)

    def update_bind_label(self, label, code, mode):
        self.is_binding = False
        self.last_bind_time = time.time()
        btn = None
        if mode == "trigger_left": btn = self.btn_bind_left
        elif mode == "trigger_right": btn = self.btn_bind_right
        elif mode == "hide": btn = self.btn_hide
        elif mode == "target":
            btn = self.btn_target
            self.saved_target_code = code
            self.saved_target_name = label
            self.backend_config({'target_btn': code})
        if btn: btn.set_label(label)
