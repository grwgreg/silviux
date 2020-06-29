import os
import threading
import time

class Notify():
    def __init__(self, context, for_test=False):
        if for_test:
            context.notify = self.fake_notify
            self.messages = []
        else:
            context.notify = self.notify
            self.last_notify = time.time()
            threading.Thread(target=self.guard_timeout).start()

    #TODO, bug where notify is called twice in loop and it overwrites
    #concat messages as easiest solution, can use the afterware function, gives all mw chance to call notify
    #also probably a good idea to use python package for dbus instead of this because of os.system (security or even accidental transcript of "&& rm file")
    def notify(self, msg, method="setText"):
        self.last_notify = time.time()
        dbusCommand = "gdbus call --session --dest org.gnome.Shell --object-path /com/gweisman/TextInTaskBar --method com.gweisman.TextInTaskBar.%s '%s'" % (method, msg,)
        os.system(dbusCommand)

    def fake_notify(self, msg, method="setText"):
        dbusCommand = "gdbus call --session --dest org.gnome.Shell --object-path /com/gweisman/TextInTaskBar --method com.gweisman.TextInTaskBar.%s '%s'" % (method, msg,)
        self.messages.append(dbusCommand)

    def guard_timeout(self):
        while True:
            #clear messages after 5 seconds
            if time.time() - self.last_notify > 5:
                self.notify('', method='setText')
            time.sleep(1)


    def middleware(self, nxt):
        def handle(context):
            msg = context.msg

            if 'clear_notify' in msg:
                self.notify('', method='setText')
                self.notify('', method='setSecondary')
                self.notify('', method='setParser')

            if 'notify' in msg:
                self.notify(msg['notify'], method='setText')

            return nxt(context)
        return handle
