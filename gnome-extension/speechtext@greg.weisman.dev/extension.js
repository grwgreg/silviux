const St = imports.gi.St;
const Main = imports.ui.main;
const Tweener = imports.ui.tweener;
const Gio = imports.gi.Gio;
const Lang = imports.lang;

const GLib = imports.gi.GLib;

//https://github.com/satya164/gjs-helpers/blob/master/src/timing.js
const setTimeout = (func, millis) => {
  return GLib.timeout_add(GLib.PRIORITY_DEFAULT, millis, () => {
    func();
    return false; // Don't repeat
  }, null);
};

const clearTimeout = id => GLib.Source.remove(id);

const setInterval = (func, millis) => {
  let id = GLib.timeout_add(GLib.PRIORITY_DEFAULT, millis, () => {
    func();
    return true; // Repeat
  }, null);

  return id;
};

const clearInterval = id => GLib.Source.remove(id);

let speechText
let parserText
let secondaryText
let secondaryPending
let textDBusService = null;

const TextInTaskBarIface = '<node> \
  <interface name="com.gweisman.TextInTaskBar"> \
  <method name="setParser"> \
  <arg type="s" direction="in" /> \
  </method> \
  <method name="setText"> \
  <arg type="s" direction="in" /> \
  </method> \
  <method name="setSecondary"> \
  <arg type="s" direction="in" /> \
  </method> \
  <method name="setTextStyle"> \
  <arg type="s" direction="in" /> \
  </method> \
  <method name="setParserStyle"> \
  <arg type="s" direction="in" /> \
  </method> \
  </interface> \
  </node>';

const TextInTaskBar = new Lang.Class({
  Name: 'TextInTaskBar',

  _init: function() {
    this._dbusImpl = Gio.DBusExportedObject.wrapJSObject(TextInTaskBarIface, this);
    this._dbusImpl.export(Gio.DBus.session, '/com/gweisman/TextInTaskBar');
  },

  setText: function(str) {
    speechText.text = str;
  },

  setSecondary: function(str) {
    secondaryText.text = str;
    if (secondaryPending) {
      clearTimeout(secondaryPending)
    }
    secondaryPending = setTimeout(function() {
      secondaryText.text = '';
    }, 1000);
  },

  setTextStyle: function(str) {
    if (str == 'error') {
      speechText.add_style_class_name('speechtext-error');
      speechText.remove_style_class_name('speechtext-final');
    } else if (str === 'final') {
      speechText.add_style_class_name('speechtext-final');
      speechText.remove_style_class_name('speechtext-error');
    } else {
      speechText.remove_style_class_name('speechtext-error');
      speechText.remove_style_class_name('speechtext-final');
    }
  },

  setParser: function(str) {
    parserText.text = str;
  },

  setParserStyle: function(str) {
    if (str == 'on') {
      parserText.add_style_class_name('parser-on');
      parserText.remove_style_class_name('parser-optimistic');
    } else if (str == 'optimistic') {
      parserText.add_style_class_name('parser-optimistic');
      parserText.remove_style_class_name('parser-on');
    } else {
      parserText.remove_style_class_name('parser-on');
      parserText.remove_style_class_name('parser-optimistic');
    }
  },
});

function init() {
  speechText = new St.Label({ style_class: 'speechtext-label', text: "" });
  parserText = new St.Label({ style_class: 'parser-label', text: "" });
  secondaryText = new St.Label({ style_class: 'secondary-label', text: "" });

  textDBusService = new TextInTaskBar();
}

function enable() {
  Main.panel._leftBox.insert_child_at_index(parserText, 2);
  Main.panel._leftBox.insert_child_at_index(speechText, 3);
  Main.panel._leftBox.insert_child_at_index(secondaryText, 4);
  log("speech text reloaded")
}

function disable() {
  Main.panel._leftBox.remove_child(parserText);
  Main.panel._leftBox.remove_child(speechText);
  Main.panel._leftBox.remove_child(secondaryText);
}
