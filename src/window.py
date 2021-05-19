# window.py
#
# Copyright 2021 Roshan-R
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from gi.repository import Gtk, Gdk, GLib, GObject
import re
import os
import subprocess
import shlex

import requests
import threading

class GAsyncSpawn(GObject.GObject):
    """GObject class to wrap GLib.spawn_async().

    Use:
        s = GAsyncSpawn()
        s.connect('process-done', mycallback)
        s.run(command)
            #command: list of strings
    """

    __gsignals__ = {
        "process-done": (
            GObject.SIGNAL_RUN_LAST,
            GObject.TYPE_NONE,
            (GObject.TYPE_INT,),
        ),
        "stdout-data": (
            GObject.SIGNAL_RUN_LAST,
            GObject.TYPE_NONE,
            (GObject.TYPE_STRING,),
        ),
        "stderr-data": (
            GObject.SIGNAL_RUN_LAST,
            GObject.TYPE_NONE,
            (GObject.TYPE_STRING,),
        ),
    }

    def __init__(self):
        GObject.GObject.__init__(self)

    def run(self, cmd):
        r = GLib.spawn_async(
            cmd,
            flags=GLib.SPAWN_DO_NOT_REAP_CHILD,
            standard_output=True,
            standard_error=True,
        )
        self.pid, idin, idout, iderr = r
        fout = os.fdopen(idout, "r")
        ferr = os.fdopen(iderr, "r")

        GLib.child_watch_add(self.pid, self._on_done)
        GLib.io_add_watch(fout, GLib.IO_IN, self._on_stdout)
        GLib.io_add_watch(ferr, GLib.IO_IN, self._on_stderr)
        return self.pid

    def _on_done(self, pid, retval, *argv):
        self.emit("process-done", retval)

    def _emit_std(self, name, value):
        self.emit(name + "-data", value)

    def _on_stdout(self, fobj, cond):
        self._emit_std("stdout", fobj.readline())
        return True

    def _on_stderr(self, fobj, cond):
        self._emit_std("stderr", fobj.readline())
        return True


@Gtk.Template(resource_path="/com/github/Roshan_R/dwnpy/window.ui")
class DwnpyWindow(Gtk.ApplicationWindow):
    __gtype_name__ = "DwnpyWindow"

    stack = Gtk.Template.Child()

    main_stack = Gtk.Template.Child()
    loading_stack = Gtk.Template.Child()
    result_stack = Gtk.Template.Child()

    # print(main_stack.label)

    label = Gtk.Template.Child()
    btn_search = Gtk.Template.Child()
    btn_back = Gtk.Template.Child()
    btn_download = Gtk.Template.Child()
    btn_cancel = Gtk.Template.Child()

    spinner = Gtk.Template.Child()
    inp_text = Gtk.Template.Child()
    inp_box = Gtk.Template.Child()
    result_image = Gtk.Template.Child()
    result_title = Gtk.Template.Child()

    progressbar = Gtk.Template.Child()

    def download_handler(self, btn):
        # thread.start_new_thread(self.download("idk"))
        self.download_thread = threading.Thread(target=self.download, args=(1,))
        # self.download_thread = StoppableThread(target=self.download, args=(1,))
        self.download_thread.start()

    def cancel_download(self, btn):
        if not self.process.poll():
            self.process.terminate()
        self.btn_download.show()
        self.btn_cancel.hide()
        self.progressbar.set_fraction(0.0)
        self.progressbar.hide()
        print("stopped process")

    def download(self, btn):
        # command = ['/usr/bin/youtube-dl', '--newline', self.link]
        command = 'youtube-dl --newline {}'.format(self.link)
        self.progressbar.show()

        # r = GLib.spawn_async(
            # command,
            # flags=GLib.SPAWN_DO_NOT_REAP_CHILD,
            # standard_output=True,
            # standard_error=True,
        # )
        # pid, idin, idout, iderr = r
        # fout = os.fdopen(idout, "r")
        # https://www.youtube.com/watch?v=L-9s4nTLSdA
        self.process = subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE)
        self.btn_download.hide()
        self.btn_cancel.show()
        while True:
            output = self.process.stdout.readline()
            if output == "" and self.process.poll() is not None:
                break
            if output:
                a = re.search(r"\[download\][\W]*([0-9]*\.[0-9])%", output.strip().decode())
                if a:
                    num = a.groups()[0]
                    fl = float(num) / 100
                    print(fl)
                    self.progressbar.set_fraction(fl)
                    print(a.groups()[0])
                # print(output.strip())
        rc = self.process.poll()
        return rc
        # while fout.readline():
            # print(fout.readline())
        # ferr = os.fdopen(iderr, "r")
        # while True:
            # output = process.stdout.readline()
            # if output == "" and process.poll() is not None:
                # break
            # if output:
                # a = re.search(
                    # r"\[download\][\W]*([0-9]*\.[0-9])%", output.strip().decode()
                # )
                # if a:
                    # print(a.groups()[0])
                    # self.progressbar.set_fraction(float(a.groups()[0]) / 10)
                # # print(output.strip())
        # rc = process.poll()
        # return rc

    def on_drag_data_received(self, widget, drag_context, x, y, data, info, time):
        self.link = data.get_text()
        print("Received text:", self.link)
        if re.search(r"http[s]*://www.youtube.com/watch\?v=(.*)", self.link):
            self.get_data("idk")

    def get_data(self, idk):

        print(self.stack.get_visible_child())
        print(self.stack.set_visible_child(self.loading_stack))
        self.spawn_title = GAsyncSpawn()
        self.spawn_title.connect("stdout-data", self.title_on_stdout_data)
        self.spawn_title.connect("stderr-data", self.title_on_stderr_data)

        # self.spawn_image = GAsyncSpawn()
        # self.spawn_image.connect("stdout-data", self.image_on_stdout_data)
        # self.spawn_image.connect("stderr-data", self.image_on_stderr_data)

        if not self.link:
            self.link = self.inp_text.get_text()
        self.label.hide()
        self.spinner.start()

        title_cmd = ["/usr/bin/youtube-dl", "-e", self.link]

        print(title_cmd)

        self.spawn_title.run(title_cmd)

        # image_cmd = [
        # "/usr/bin/youtube-dl",
        # "--list-thumbnails",
        # self.inp_text.get_text(),
        # ]

        # self.spawn_image.run(image_cmd)
        img_url = "https://i.ytimg.com/vi/{}/hqdefault.jpg".format(
            re.match(r"http[s]*://www.youtube.com/watch\?v=(.*)", self.link).groups()[0]
        )

        res = requests.get(img_url)
        open("/tmp/image.jpg", "wb").write(res.content)
        self.result_image.set_from_file("/tmp/image.jpg")
        print("image set")

    def title_on_stdout_data(self, sender, line):
        print("Hello")
        self.spinner.stop()
        self.label.set_text(line)
        self.label.show()
        print("[STDOUT]", line)
        self.result_title.set_text(line)
        self.btn_back.show()
        self.stack.set_visible_child(self.result_stack)

    def title_on_stderr_data(self, sender, line):
        self.spinner.stop()
        self.label.set_text("Could not parse the url :(")
        self.label.show()
        print("[STDERR]", line.strip("\n"))

    def image_on_stdout_data(self, sender, line):
        print("[STDOUT]", line)

    def image_on_stderr_data(self, sender, line):
        # self.spinner.stop()
        # self.label.set_text("Could not parse the url :(")
        # self.label.show()
        print("[STDERR]", line.strip("\n"))

    def reset_things(self, btn):
        self.stack.set_visible_child(self.main_stack)
        self.btn_back.hide()
        self.label.set_text("Drop Urls here or type down below")
        self.link = ""
        # self.label.clear()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        print(self.label)
        self.link = ""
        enforce_target = Gtk.TargetEntry.new("text/plain", Gtk.TargetFlags(4), 129)
        self.label.drag_dest_set(
            Gtk.DestDefaults.ALL, [enforce_target], Gdk.DragAction.COPY
        )

        self.label.connect("drag-data-received", self.on_drag_data_received)
        self.btn_search.connect("clicked", self.get_data)

        self.btn_back.connect("clicked", self.reset_things)
        self.btn_back.hide()

        self.btn_download.connect("clicked", self.download_handler)

        self.btn_cancel.connect("clicked", self.cancel_download)
        self.progressbar.hide()
        # GLib.idle_add(self.download)
