import Gio from 'gi://Gio';
import GLib from 'gi://GLib';
import Meta from 'gi://Meta';
import Shell from 'gi://Shell';
import {Extension} from 'resource:///org/gnome/shell/extensions/extension.js';
import * as Main from 'resource:///org/gnome/shell/ui/main.js';

const XML = `<node><interface name="org.lookup.Linux.Gnome">
<method name="State"><arg type="s" direction="out"/></method>
<method name="Capture"><arg type="s" direction="in"/><arg type="s" direction="out"/></method>
<method name="Place"><arg type="i" direction="in"/><arg type="s" direction="in"/>
<arg type="i" direction="in"/><arg type="i" direction="in"/><arg type="b" direction="out"/></method>
<method name="SetShortcut"><arg type="s" direction="in"/><arg type="s" direction="in"/>
<arg type="b" direction="out"/></method>
</interface></node>`;

export default class LookUp extends Extension {
    enable() {
        this._action = 0;
        this._shortcut = '';
        this._capturing = false;
        this._settings = this.getSettings();
        this._dbus = Gio.DBusExportedObject.wrapJSObject(XML, this);
        this._dbus.export(Gio.DBus.session, '/org/lookup/Linux/Gnome');
        this._signal = global.display.connect('accelerator-activated', (_display, action) => {
            if (action === this._action)
                Gio.DesktopAppInfo.new('org.lookup.Linux.desktop')?.launch([], null);
        });
        this._setShortcut(this._settings.get_string('shortcut'), this._settings.get_string('accelerator'));
    }

    disable() {
        this._dbus?.unexport();
        this._dbus = null;
        if (this._signal)
            global.display.disconnect(this._signal);
        this._signal = 0;
        if (this._action)
            global.display.ungrab_accelerator(this._action);
        this._action = 0;
        this._shortcut = '';
        this._settings = null;
    }

    State() {
        if (Main.sessionMode.isLocked)
            throw new Error('Session locked');
        const [x, y] = global.get_pointer();
        return JSON.stringify({version: 1, point: [x, y], shortcut: this._shortcut,
            monitors: Main.layoutManager.monitors.map(m => {
                const work = global.workspace_manager.get_active_workspace().get_work_area_for_monitor(m.index);
                return {name: String(m.index), x: m.x, y: m.y, width: m.width, height: m.height,
                    scale: global.display.get_monitor_scale(m.index),
                    available: [work.x, work.y, work.width, work.height]};
            })});
    }

    async CaptureAsync([name], invocation) {
        let stream;
        let acquired = false;
        try {
            await this._owner(invocation);
            const monitor = Main.layoutManager.monitors.find(m => String(m.index) === name);
            if (!monitor || this._capturing || Main.sessionMode.isLocked)
                throw new Error('Unavailable');
            this._capturing = true;
            acquired = true;
            stream = Gio.MemoryOutputStream.new_resizable();
            const shooter = new Shell.Screenshot();
            await new Promise((resolve, reject) => {
                shooter.screenshot_area(monitor.x, monitor.y, monitor.width, monitor.height, stream,
                    (obj, result) => {
                        try { obj.screenshot_area_finish(result); resolve(); }
                        catch (error) { reject(error); }
                    });
            });
            stream.close(null);
            const bytes = stream.steal_as_bytes();
            if (bytes.get_size() > 64 * 1024 * 1024 || !this._dbus || Main.sessionMode.isLocked)
                throw new Error('Unavailable');
            invocation.return_value(new GLib.Variant('(s)', [GLib.base64_encode(bytes.get_data())]));
        } catch (_error) {
            invocation.return_dbus_error('org.lookup.Linux.CaptureFailed', 'Screen capture unavailable');
        } finally {
            stream?.close(null);
            if (acquired)
                this._capturing = false;
        }
    }

    async _owner(invocation) {
        const result = await new Promise((resolve, reject) => {
            Gio.DBus.session.call('org.freedesktop.DBus', '/org/freedesktop/DBus',
                'org.freedesktop.DBus', 'GetNameOwner', new GLib.Variant('(s)', ['org.lookup.Linux']),
                new GLib.VariantType('(s)'), Gio.DBusCallFlags.NONE, 1000, null,
                (bus, res) => {
                    try { resolve(bus.call_finish(res)); }
                    catch (error) { reject(error); }
                });
        });
        if (result.deep_unpack()[0] !== invocation.get_sender() || !this._dbus || Main.sessionMode.isLocked)
            throw new Error('Not the LookUp application');
    }

    async PlaceAsync([pid, title, x, y], invocation) {
        try {
            await this._owner(invocation);
            invocation.return_value(new GLib.Variant('(b)', [this._place(pid, title, x, y)]));
        } catch (_error) {
            invocation.return_dbus_error('org.lookup.Linux.AccessDenied', 'LookUp application required');
        }
    }

    _place(pid, title, x, y) {
        if (pid <= 0 || Main.sessionMode.isLocked)
            return false;
        const window = global.get_window_actors().map(a => a.meta_window)
            .find(w => w.get_pid() === pid && w.get_title() === title);
        if (!window)
            return false;
        window.move_frame(true, x, y);
        window.raise();
        Main.activateWindow(window);
        return true;
    }

    async SetShortcutAsync([text, accelerator], invocation) {
        try {
            await this._owner(invocation);
            const ok = this._setShortcut(text, accelerator);
            if (ok) {
                this._settings.set_string('shortcut', text);
                this._settings.set_string('accelerator', accelerator);
            }
            invocation.return_value(new GLib.Variant('(b)', [ok]));
        } catch (_error) {
            invocation.return_dbus_error('org.lookup.Linux.AccessDenied', 'LookUp application required');
        }
    }

    _setShortcut(text, accelerator) {
        if (text === this._shortcut)
            return true;
        if (text.length > 128 || accelerator.length > 128)
            return false;
        let action = 0;
        if (accelerator) {
            action = global.display.grab_accelerator(accelerator, Meta.KeyBindingFlags.NONE);
            if (!action)
                return false;
            Main.wm.allowKeybinding(Meta.external_binding_name_for_action(action), Shell.ActionMode.NORMAL);
        }
        if (this._action)
            global.display.ungrab_accelerator(this._action);
        this._action = action;
        this._shortcut = text;
        return true;
    }
}
