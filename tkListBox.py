# -*- coding: utf-8 -*-
import tkinter as tk


class tkListBox:

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Being Studio")
        self.root.geometry("400x260+0+0")
        self.root.attributes('-topmost', True)
        self.root.maxsize(0, 0)
        self.root.resizable(0, 0)
        scrollbar = tk.Scrollbar(self.root)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox = tk.Listbox(self.root, width=390, height=250, yscrollcommand=scrollbar.set)

        self.data = {
            0: '',
            1: u'##全  場 - ',
            2: u'##角  球 - ',
            3: u'##十五分 - ',
            4: u'##波  膽 - ',
            5: u'##入球數 - ',
            6: u'##半全場 - ',
        }

    def insert(self, _index, _str):
        # noinspection PyBroadException
        try:
            self.listbox.insert(_index, self.data[_index] + _str)
        except Exception:
            print('insert error')


    def undate(self, _index, _str):
        # noinspection PyBroadException
        try:
            self.listbox.delete(_index)
            self.listbox.insert(_index, self.data[_index] + _str)
        except Exception:
            print('undate error')


    def getTitle(self, _index):
        _str = self.listbox.get(_index)
        pos = _str.find(' - ') + 3
        return _str[0:pos]

    def start(self):
        self.listbox.pack()
        self.root.mainloop()
