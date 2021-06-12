from tkinter import *
import time
import os
import shutil


class VerticalScrolledFrame(Frame):

    def __init__(self, parent, iData, *args, **kw):
        Frame.__init__(self, parent, *args, **kw)
        width = 400
        height = 200 + iData * 50
        # create a canvas object and a vertical scrollbar for scrolling it
        vscrollbar = Scrollbar(self, orient=VERTICAL)
        vscrollbar.pack(fill=Y, side=RIGHT, expand=FALSE)
        canvas = Canvas(self, bd=0, highlightthickness=0, yscrollcommand=vscrollbar.set, bg='red')
        canvas.pack(side=LEFT, fill=BOTH, expand=TRUE)
        vscrollbar.config(command=canvas.yview)

        # reset the view
        canvas.xview_moveto(0)
        canvas.yview_moveto(0)

        # create a frame inside the canvas which will be scrolled with it
        self.interior = interior = Frame(canvas)
        interior_id = canvas.create_window(0, 0, window=interior, anchor=NW)

        # track changes to the canvas and frame width and sync them,
        # also updating the scrollbar
        def _configure_interior(event):
            # update the scrollbars to match the size of the inner frame
            size = (interior.winfo_reqwidth(), interior.winfo_reqheight())
            canvas.config(scrollregion="0 0 %s %s" % size)
            if interior.winfo_reqwidth() != canvas.winfo_width():
                # update the canvas's width to fit the inner frame
                # canvas.config(width=interior.winfo_reqwidth())
                canvas.config(width=width, height=height)

        interior.bind('<Configure>', _configure_interior)

        def _configure_canvas(event):
            if interior.winfo_reqwidth() != canvas.winfo_width():
                # update the inner frame's width to fill the canvas
                # canvas.itemconfigure(interior_id, width=canvas.winfo_width())
                canvas.itemconfigure(interior_id, width=width, height=height)

        canvas.bind('<Configure>', _configure_canvas)

        path = 'logs\\label'
        try:
            shutil.rmtree(path)
            path = 'logs'
            if not os.path.isdir(path):
                os.mkdir(path)
            path = 'logs\\label'
            if not os.path.isdir(path):
                os.mkdir(path)
        except OSError as e:
            print(e)



class tkLabel():
    def __init__(self, _data, _globData):
        self.data = _data
        self.globData = _globData

    def update_clock(self):
        # noinspection PyBroadException
        try:
            now = time.strftime("%H:%M:%S")
            self.label_msg1.configure(text='現在時間:' + now)
            if int(float(time.time())) > int(float(self.globData['timestamp_end'])):
                self.label_msg1.configure(text='現在時間:' + now + " - 腳本已終止")
                if self.globData['is_test'] != "TRUE":
                    self.root.quit()  # 關閉訊息框
            else:
                self.root.after(500, self.update_clock)
            self.readLabel()
        except Exception as e:
            print("update_clock error")
            self.root.quit()  # 關閉訊息框

    def readLabel(self):
        # noinspection PyBroadException
        try:
            for index in self.data:
                txt_url = "logs\\label\\label_" + str(index) + '.txt'
                f = open(txt_url, 'r')
                msg = f.read()
                f.close()
                self.data[index]['label'].configure(text=msg)
        except Exception:
            time.sleep(0.01)

    def updateLabel(self, index, msg):
        # noinspection PyBroadException
        try:
            txt_url = "logs\\label\\label_" + str(index) + '.txt'
            f = open(txt_url, "w")
            f.write(msg + '\n')
            f.close()
        except Exception as e:
            print("update error")
            print(e)
            # self.root.quit()  # 關閉訊息框
        # # noinspection PyBroadException
        # try:
        #     self.data[index]['label'].configure(text=msg)
        # except Exception:
        #     print("update error")
        #     self.root.quit()  # 關閉訊息框

    def start(self):
        self.root = Tk()
        self.root.title("Being Studio")
        self.root.geometry("400x800+0+0")
        self.root.attributes('-topmost', True)
        # self.root.maxsize(0, 0)
        # self.root.resizable(0, 0)
        self.frame = VerticalScrolledFrame(self.root, len(self.data))
        self.frame.pack()
        self.label = Label(text="©Copyright 2021-05 Being Studio.")
        self.label.pack()

        label_title = Label(self.frame.interior, text="", fg="Blue", font=("Helvetica", 16))
        label_title.pack()
        label_title.configure(text=self.globData['account'])

        self.label_msg = Label(self.frame.interior, text="", font=("Helvetica", 14))
        self.label_msg.pack()

        start_time = time.strftime("%H:%M:%S")
        end_time = time.strftime("%H:%M:%S", time.localtime(self.globData['timestamp_end']))  # 轉成字串
        self.label_msg.configure(text='開始時間:' + start_time + ' , 結束時間:' + end_time)

        self.label_msg1 = Label(self.frame.interior, text="", font=("Helvetica", 14))
        self.label_msg1.pack()

        for one in self.data:
            print(self.data[one]['title'])
            label_1 = Label(self.frame.interior, text="", fg="SeaGreen", font=("Helvetica", 12))
            label_1.pack()
            label_1.configure(text=self.data[one]['title'] + "-" + self.data[one]['game']['title'])
            label_2 = Label(self.frame.interior, text="", font=("Helvetica", 10))
            label_2.pack()
            label_2.configure(text="")
            self.data[one]['label'] = label_2

        self.start_time = time.strftime("%H:%M:%S")
        print(self.data)
        self.update_clock()
        self.root.mainloop()

# root = Tk()
# app = App(root)
# root.wm_title("Being Studio")
# root.geometry("400x300")
# root.after(1000, app.update_clock)
# root.mainloop()
# tk2 = App()
# tk2.start()
