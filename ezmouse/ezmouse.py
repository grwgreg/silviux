#Modify the area_draw method rgba values to mess with background transparency & color of overlay
#Css is used for font style & size, search for 'font' in this file
#https://stackoverflow.com/questions/21974755/gtk3-button-how-to-set-font-size
#https://askubuntu.com/questions/93088/making-gtk-window-transparent
import cairo
import itertools
import string
import gi
gi.require_version('Gtk', '3.0') 
from gi.repository import Gtk, Gdk
from subprocess import Popen, PIPE

class EZMouse(Gtk.Window):
    def __init__(self):
        super(EZMouse, self).__init__()
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_border_width(0)
        self.screen = self.get_screen()
        self.maximize()
        self.visual = self.screen.get_rgba_visual()
        self.set_decorated(False)
        self.set_resizable(False)  
        if self.visual != None and self.screen.is_composited():
            self.set_visual(self.visual)

        grid = Gtk.Grid()
        #homogenous layout spreads across like flexbox
        grid.set_row_homogeneous(True)
        grid.set_column_homogeneous(True)
        self.add(grid)

        #last number keypress saved and output with result
        #in standalone.py I use this to distinguish between clicks/doubleclicks etc
        self.last_digit = -1
        self.level = 0
        #levels is array of dicts, [{char: [label]}]
        #each dict stores visible labels index by their char
        #the labels carry some state about what level they were hidden
        #and their char at each level so that state can be restored
        self.levels = []
        self.char_stream = itertools.cycle(string.ascii_uppercase)

        #for level 0 with 2 character labels
        self.char_pairs = []
        for x in string.ascii_uppercase:
            for y in string.ascii_uppercase:
                self.char_pairs.append(x+y)
        self.char_pair_stream = itertools.cycle(self.char_pairs)

        #for levels with multiple letter labels we build this up before calling descend
        self.last_keys = ''

        self.init_labels(grid)

#css stuff
        gtk_provider = Gtk.CssProvider()
        gtk_context = Gtk.StyleContext()
        gtk_context.add_provider_for_screen(self.screen, gtk_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        #calling set_visible(False) on label causes all letters to shift left for some reason
        #but transparent css color works
        #https://developer.gnome.org/gtk3/stable/chap-css-properties.html
        css = """
label {
    color: pink;
    font-size: 9;
    font-weight: bold;
}

label:nth-child(odd) {
  color: yellow
}

.yellow label {
    color: yellow;
}

label.hidden {
    color: transparent;
}
"""
        gtk_provider.load_from_data(css)


        self.connect("key-press-event",self.on_key)

        self.set_app_paintable(True)
        self.connect("draw", self.area_draw)
        self.connect("destroy", Gtk.main_quit)
        self.show_all()

    def area_draw(self, widget, cr):
        #last value is alpha (transparency)
        cr.set_source_rgba(.2, .2, .2, 0.3)
        cr.set_operator(cairo.OPERATOR_SOURCE)
        cr.paint()
        cr.set_operator(cairo.OPERATOR_OVER)

    #originally this was to change colors by level
    #but now only 2 levels and obvious because 2char vs 1char label
    def toggle_color(self):
        style_context = self.get_style_context()
        if self.level % 2 == 0:
            style_context.add_class('yellow')
        else:
            style_context.remove_class('yellow')

    def init_labels(self, grid):
        labels = {}
        for ch in self.char_pairs:
            labels[ch] = []

        #x,y ranges are how many chars to display 
        #the set_homogenous on grid should spread them out evenly
        #but I found at some random large number the layout will get weird and
        #off center (maybe gnome trying to spread across all screens or something)
# for font size 12 this is good:
        for y in range(36):
            for x in range(85):
#adding more labels takes an extra second or so longer to load... :(
#could alter this to be long running and simply minimize/maximize to activate
#hold off on this because I think making this a gnome extension makes more sense
#        for y in range(70):
#            for x in range(101):
                ch = next(self.char_pair_stream)
                label = Gtk.Label(ch)
                label.hidden = False
                label.chars_by_level = [ch]
                labels[ch].append(label)
                grid.attach(label, x, y, 1, 1)

        self.levels.append(labels)

	#todo refactor
    def descend(self, typed):
        level = self.levels[self.level]
        if typed not in level:
            return
        if len(level[typed]) == 1:
            return self.handle_hit(level[typed][0])
        self.toggle_color()
        next_level = {}
        for l, labels in list(level.items()):
			#hide all other visible typeds
            if l != typed:
                for label in labels:
                    if not label.hidden:
                        style_context = label.get_style_context()
                        style_context.add_class('hidden')
                        label.hidden = True
                        label.last_visible = self.level
			#update chars on all matching labels
            else:
                for label in labels:
                    if not label.hidden:
                        next_typed = next(self.char_stream)
                        label.chars_by_level.append(next_typed)
                        label.set_label(next_typed)
                        if next_typed not in next_level:
                            next_level[next_typed] = []
                        next_level[next_typed].append(label)
        self.level += 1
        self.levels.append(next_level)

    def ascend(self):
        if self.level == 0: return
        last_level = self.levels.pop()
        #rewind visible labels state
        self.toggle_color()
        for l, labels in list(last_level.items()):
            for label in labels:
                del label.chars_by_level[self.level]
                last_typed = label.chars_by_level[self.level - 1]
                label.set_label(last_typed)

        #show previously hidden labels
        self.level -= 1
        level = self.levels[self.level]
        for l, labels in list(level.items()):
            for label in labels:
                if label.hidden and label.last_visible == self.level:
                    style_context = label.get_style_context()
                    style_context.remove_class('hidden')
                    label.hidden = False
                    del label.last_visible

    def handle_hit(self, label):
        #the gnome taskbar isnt accounted for from the gtk api stuff, 0,0 is below taskbar
        #TODO maybe a cleaner way?
        #$xdotool getactivewindow getwindowgeometry

#can call get_allocation on window obj too, should be 0,0 though
#        print 'window: ',self.get_allocation().x
#        print 'window: ',self.get_allocation().y
        process = Popen(["xdotool", "getactivewindow", "getwindowgeometry"], stdout=PIPE)
        (geo, err) = process.communicate()
        process.wait()

        #yuck
        position_output = geo.split("\n")[1]
        start = position_output.find("Position:") + 10 
        end = position_output.find("(")
        win_x, win_y = position_output[start:end].split(",")

        x = label.get_allocation().x
        y = label.get_allocation().y
        width = label.get_allocation().width
        height = label.get_allocation().height

        #just parse stdout for results I think...
        #TODO this is probably better as a gnome extension... not sure drag/drop
        #is doable since this window will display above what the mouse is holding down on?
        #look into setting to always be on top?
        #xdotool lets you send keystrokes to a specific window but dragging between windows
        #probably breaks?
        #could also save the coords and compose an xmacro on the fly for drag drop..
        print(int(win_x) + x + (width/2))
        print(int(win_y) + y + (height/2))
        print(self.last_digit)
        print(self.last_was_uppercase)
        Gtk.main_quit()

    def on_key(self, widget, key):
        if not key.string.isalpha(): 
#            print key.string
#            print dir(key)
#            print 'code', key.get_keycode()
#            print 'val', key.get_keyval()
            _, keycode =  key.get_keycode()
            if key.string.isdigit():
                self.last_digit = int(key.string)
            #esc key
            if keycode == 66:
                Gtk.main_quit()
            #backspace
            if keycode == 22:
                self.ascend()
            return
        self.last_was_uppercase = key.string.isupper()
        chars = key.string.upper()
        #todo, first level now has 2 character label
        #make this more general? 3+ chars or multiple levels of many chars?
        if self.level == 0:
            if len(self.last_keys) == 0:
                self.last_keys = key.string.upper()
                return
            chars = self.last_keys + key.string.upper()
            self.last_keys = ''
        self.descend(chars)

if __name__ == '__main__':
    window = EZMouse()
    Gtk.main()
