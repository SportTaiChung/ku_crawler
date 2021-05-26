import tkinter as tk
import time


class tkLabel():
    def __init__(self, _oBtnSC, _globData):
        self.data = _oBtnSC
        self.globData = _globData

    def update_clock(self):
        # noinspection PyBroadException
        try:
            now = time.strftime("%H:%M:%S")
            self.label_msg1.configure(text='現在時間:' + now)
            if int(float(time.time())) > int(float(self.globData['timestamp_end'])):
                self.label_msg1.configure(text='現在時間:' + now + " - 腳本已終止")
                if self.globData['is_test'] != "True":
                    self.root.quit()  # 關閉訊息框
            else:
                self.root.after(1000, self.update_clock)
        except Exception as e:
            print("update_clock error")
            self.root.quit()  # 關閉訊息框

    def updateLabel(self, index, msg):
        # noinspection PyBroadException
        try:
            self.data[index]['label'].configure(text=msg)
        except Exception:
            print("update error")
            self.root.quit()  # 關閉訊息框

    def start(self):
        self.root = tk.Tk()
        self.root.title("Being Studio")
        dataLen = str(len(self.data) * 70)
        self.root.geometry("400x" + dataLen + "+0+0")
        self.root.attributes('-topmost', True)
        self.root.maxsize(0, 0)
        self.root.resizable(0, 0)

        label_title = tk.Label(text="", fg="Blue", font=("Helvetica", 18))
        label_title.pack()
        label_title.configure(text=u"足球 - " + self.globData['account'])

        self.label_msg = tk.Label(text="", font=("Helvetica", 16))
        self.label_msg.pack()
        start_time = time.strftime("%H:%M:%S")
        end_time = time.strftime("%H:%M:%S", time.localtime(self.globData['timestamp_end']))  # 轉成字串
        self.label_msg.configure(text='開始時間:' + start_time + ' , 結束時間:' + end_time)
        self.label_msg1 = tk.Label(text="", font=("Helvetica", 16))
        self.label_msg1.pack()

        for one in self.data:
            label_1 = tk.Label(text="", font=("Helvetica", 12))
            label_1.pack()
            label_1.configure(text=self.data[one]['title'])
            label_2 = tk.Label(text="", font=("Helvetica", 10))
            label_2.pack()
            label_2.configure(text="")
            self.data[one]['label'] = label_2

        self.start_time = time.strftime("%H:%M:%S")
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
