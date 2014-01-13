from Tkinter import *
from PIL import Image, ImageTk
root = Tk()
image = Image.open("image.jpg")
photo = ImageTk.PhotoImage(image)
label = Label(root, image=photo)
label.pack()
root.mainloop()
