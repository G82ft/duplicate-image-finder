import os
import shutil
from tkinter import IntVar, StringVar
from tkinter import Tk, Toplevel, Frame, Label, Entry, Menubutton, Menu, Button
from tkinter.ttk import Progressbar
from tkinter.messagebox import showerror, showinfo

import PIL
from PIL import Image, ImageChops
from PIL.ImageTk import PhotoImage


def validate_path(entry, path) -> bool:
    if not os.path.exists(path):
        entry['bg'] = 'pink'
    else:
        entry['bg'] = '#f9f9f9'
    return True


class LoadingWindow:
    def __init__(self, title: str = 'Loading...', size: int = 100):
        self.root: Toplevel = Toplevel()
        self.root.title(title)
        self.root.geometry('250x125')

        for i in range(4):
            self.root.rowconfigure(i, weight=1)
            if i != 3:
                self.root.columnconfigure(i, weight=1)

        Label(
            self.root,
            text=title,
            justify='left'
        ).grid(row=1, column=1,
               sticky='w')

        self.pb: Progressbar = Progressbar(
            self.root,
            maximum=size,
            mode='indeterminate'
        )
        self.pb.grid(row=2, column=1,
                     sticky='ew')

    def step(self) -> None:
        self.pb.step()

    def destroy(self) -> None:
        self.root.destroy()


class Root:
    def __init__(self):
        self.images: list = []
        self.selected: list = []
        self.min_res: int = 0

        self.root: Tk = Tk()
        self.root.title('Duplicated image finder')
        self.root.geometry('500x300')
        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)

        frame: Frame = Frame(
            self.root,
            relief='ridge',
            bd=5
        )
        frame.grid(sticky='nesw')

        for i in range(3):
            frame.columnconfigure(i, weight=1)

        line_num: int = 0

        line_num += 1
        Label(
            frame,
            text='Path to scan',
            justify='left'
        ).grid(row=line_num, column=1,
               sticky='sw')

        line_num += 1
        self.sp: Entry = Entry(
            frame,
            validate='key'
        )
        self.sp['validatecommand'] = self.root.register(lambda path, ew=self.sp: validate_path(ew, path)), '%P'
        self.sp.grid(row=line_num, column=1,
                     sticky='nwe')
        self.sp.bind('<Return>', self.fast_scan)

        Button(
            frame,
            text='Fast scan',
            command=self.fast_scan,
        ).grid(row=line_num - 1, column=1,
               sticky='se')

        line_num += 1
        Label(
            frame,
            text='Shrink images to'
        ).grid(row=line_num, column=1,
               sticky='sw')

        line_num += 1
        self.shrink: StringVar = StringVar()
        self.se: Entry = Entry(
            frame,
            state='readonly',
            textvariable=self.shrink,
            validate='key',
            validatecommand=(self.root.register(lambda res: res.isdigit() if res else True), '%P')
        )
        self.se.grid(row=line_num, column=1,
                     sticky='nwe')
        self.se.bind('<Return>', self.scan)

        Button(
            frame,
            text='Scan',
            command=self.scan,
        ).grid(row=line_num - 1, column=1,
               sticky='se')

        line_num += 1
        self.mb: Menubutton = Menubutton(
            frame,
            text='Duplicated images',
            relief='raised'
        )
        self.mb.grid(row=line_num, column=1,
                     sticky='we')

        self.duplicate_images: StringVar = StringVar()

        line_num += 1
        Label(
            frame,
            text='Path to export selected images'
        ).grid(row=line_num, column=1,
               sticky='sw')

        line_num += 1
        self.export: StringVar = StringVar()
        ep = Entry(
            frame,
            validate='key',
            textvariable=self.export
        )
        ep['validatecommand'] = self.root.register(
            lambda path, ew=ep:
            validate_path(ew, path) if not path.endswith('Better images')
            else validate_path(ew, path.replace('Better images', ''))
        ), '%P'
        ep.grid(row=line_num, column=1,
                sticky='nwe')
        ep.bind('<Return>', self.export_selected)

        Button(
            frame,
            text='Export selected',
            command=self.export_selected,
        ).grid(row=line_num - 1, column=1,
               sticky='se')

        for i in range(line_num + 2):
            frame.rowconfigure(i, weight=1)

    def fast_scan(self, *_) -> None:
        scan_path: str = self.sp.get()

        if not os.access(scan_path, os.R_OK):
            showerror('Error', f'Can\'t read path for scan!')
            return None

        if not scan_path.endswith(os.sep):
            scan_path += os.sep

        res: list = []

        self.sp["state"] = 'readonly'
        export_path: str = scan_path + 'Better images'
        self.export.set(export_path)

        w: LoadingWindow = LoadingWindow('Fast scanning', 20)

        for file in os.listdir(scan_path):
            filepath: str = scan_path + file

            if os.path.isdir(filepath):
                continue
            try:
                im = Image.open(filepath)
            except PIL.UnidentifiedImageError:
                continue

            res.append(min(im.size))
            self.images.append(file)

            w.step()
            self.root.update()
            self.root.update_idletasks()

        w.destroy()

        self.min_res: int = min(res)
        self.se['state'] = 'normal'
        self.shrink.set(str(self.min_res))

        return None

    def scan(self, *_) -> None:
        duplicate_images: list[list, ...] = [[]]

        scan_path: str = self.sp.get()
        if not os.path.exists(scan_path):
            showerror('Error', 'Path for scan does not exist!')
            return None

        if not scan_path.endswith(os.sep):
            scan_path += os.sep

        if not self.shrink.get():
            self.shrink.set(str(self.min_res))
        res: int = int(self.shrink.get())
        self.se['state'] = 'readonly'

        w: LoadingWindow = LoadingWindow('Scanning', 50)

        for i, path1 in enumerate(self.images):
            im1: Image.Image = Image.open(scan_path + path1)
            im1_size: tuple[int, int] = im1.size
            im1.thumbnail((res,) * 2)
            for path2 in self.images[i + 1:]:
                im2: Image.Image = Image.open(scan_path + path2)
                im2_size: tuple[int, int] = im2.size
                im2.thumbnail((res,) * 2)

                if im1.size == im2.size:
                    im = ImageChops.subtract(im1.convert('L'), im2.convert('L'))
                    im.thumbnail((1, 1))
                    if im.getpixel((0, 0)) == 0:
                        duplicate_images[-1].append((path2, im2_size))

            if duplicate_images[-1]:
                duplicate_images[-1].insert(0, (path1, im1_size))
                duplicate_images.append([])

            w.step()
            self.root.update()
            self.root.update_idletasks()

        if not duplicate_images[-1]:
            duplicate_images.pop()

        images: Menu = Menu(
            self.mb,
            tearoff=False
        )
        for im in duplicate_images:
            im.sort(key=lambda x: x[1], reverse=True)
            sub_images: Menu = Menu(tearoff=False)
            for path, size in im:
                check_var: IntVar = IntVar()

                if size == im[0][1]:
                    check_var.set(1)
                    self.selected.append(path)

                sub_images.add_checkbutton(
                    label=path,
                    accelerator='{}x{}'.format(*size),
                    variable=check_var,
                    command=lambda im_path=path, var=check_var:
                    self.selected.append(im_path) if var.get()
                    else self.selected.remove(im_path) if im_path in self.selected
                    else None
                )

            icon = Image.open(scan_path + im[0][0])
            icon.thumbnail((50, 50))
            images.add_cascade(
                label=im[0][0],
                image=PhotoImage(icon),
                compound='left',
                menu=sub_images
            )

            w.step()
            self.root.update()
            self.root.update_idletasks()

        w.destroy()
        showinfo('Info', 'Scanning is finished.')

        self.mb["menu"] = images

    def export_selected(self, *_) -> None:
        scan_path: str = self.sp.get()

        if not scan_path.endswith(os.sep):
            scan_path += os.sep

        export_path: str = self.export.get()
        if not os.access(export_path, os.W_OK):
            if os.path.basename(export_path) != 'Better images':
                showerror('Error', 'Can\'t access export path!')
                return None

            if not os.access(os.path.dirname(export_path), os.W_OK):
                showerror('Error', 'Can\'t access export path!')
                return None

            os.mkdir(export_path)

        if not export_path.endswith(os.sep):
            export_path += os.sep

        w: LoadingWindow = LoadingWindow('Exporting', 30)

        for path in self.selected:
            shutil.copy2(scan_path + path, export_path)

            w.step()
            self.root.update()
            self.root.update_idletasks()

        w.destroy()
        showinfo('Info', 'Export finished!')


Root().root.mainloop()
