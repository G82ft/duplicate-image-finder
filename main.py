#   __                                          _
#  /  )       / ' _  _ _/ _   ' _   _  _  _   /_ '    _/ _  _
# /(_/ (/ /) ( / (  (/ / (-  / //) (/ (/ (-  /  / /) (/ (- /
#        /                           _/

"""Duplicate image finder

Made by Leonid (https://github.com/G4m3-80ft)"""

import os
import shutil
from itertools import chain
from tkinter import IntVar, StringVar
from tkinter import Tk, Toplevel, Frame, Label, Entry, Menubutton, Menu, Button
from tkinter.font import Font
from tkinter.ttk import Progressbar
from tkinter.messagebox import showerror, showinfo
from tkinter.filedialog import askdirectory

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
    def __init__(self, title: str = 'Loading...', *, size: int = 100, determinate: bool = False):
        self.root: Toplevel = Toplevel()
        self.root.title(title)
        self.root.geometry('400x125')

        for i in range(4):
            self.root.rowconfigure(i, weight=1)
            if i != 3:
                self.root.columnconfigure(i, weight=1)

        self.current_task: StringVar = StringVar()
        self.current_task.set(title)
        Label(
            self.root,
            textvariable=self.current_task,
            justify='left'
        ).grid(row=1, column=1,
               sticky='w')

        # noinspection PyTypeChecker
        self.pb: Progressbar = Progressbar(
            self.root,
            maximum=size,
            mode='determinate' if determinate else 'indeterminate'
        )
        self.pb.grid(row=2, column=1,
                     sticky='ew')

    def step(self) -> None:
        self.pb.step()

    def destroy(self) -> None:
        self.root.destroy()


class Root:
    def __init__(self):
        # noinspection PyTypeChecker
        self.image_resolutions: dict[str, tuple[int, int]] = {}
        self.selected: list[str] = []

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
        frame.grid(row=0, column=0,
                   sticky='nesw')

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

        Button(
            frame,
            text='Scan resolutions',
            command=self.scan_resolutions,
        ).grid(row=line_num, column=1,
               sticky='se')

        line_num += 1
        path_frame: Frame = Frame(
            frame
        )
        path_frame.grid(row=line_num, column=1,
                        sticky='new')
        for i in range(2):
            path_frame.columnconfigure(i, weight=1 - i)

        scan_path: StringVar = StringVar()
        self.scan_entry: Entry = Entry(
            path_frame,
            validate='key',
            textvariable=scan_path
        )
        self.scan_entry['validatecommand'] = self.root.register(
            lambda path, ew=self.scan_entry: validate_path(ew, path)
        ), '%P'
        self.scan_entry.grid(column=0,
                             sticky='nesw')
        self.scan_entry.bind('<Return>', self.scan_resolutions)
        Button(
            path_frame,
            text='Browse',
            command=lambda: scan_path.set(
                os.path.normpath(d) if (
                    d := askdirectory(
                        title='Choose path to scan',
                        initialdir=self.scan_entry.get()
                    )
                )
                else scan_path.get()
            )
        ).grid(row=0, column=1,
               sticky='e')

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
                     sticky='new')
        self.se.bind('<Return>', self.scan_duplicates)

        Button(
            frame,
            text='Scan duplicates',
            command=self.scan_duplicates,
        ).grid(row=line_num - 1, column=1,
               sticky='es')

        line_num += 1
        self.mb: Menubutton = Menubutton(
            frame,
            text='Duplicated images',
            relief='raised'
        )
        self.mb.grid(row=line_num, column=1,
                     sticky='ew')

        self.duplicate_images: StringVar = StringVar()

        line_num += 1
        Label(
            frame,
            text='Path to export selected'
        ).grid(row=line_num, column=1,
               sticky='sw')
        Button(
            frame,
            text='Export selected',
            command=self.export_selected,
        ).grid(row=line_num, column=1,
               sticky='es')

        line_num += 1
        path_frame: Frame = Frame(
            frame
        )
        path_frame.grid(row=line_num, column=1,
                        sticky='new')
        for i in range(2):
            path_frame.columnconfigure(i, weight=1 - i)

        self.export: StringVar = StringVar()
        export_entry = Entry(
            path_frame,
            validate='key',
            textvariable=self.export
        )
        export_entry['validatecommand'] = self.root.register(
            lambda path, ew=export_entry:
            validate_path(ew, path) if not path.endswith('better-images')
            else validate_path(ew, path.replace('better-images', ''))
        ), '%P'
        export_entry.grid(row=0, column=0,
                          sticky='nesw')
        export_entry.bind('<Return>', self.export_selected)

        Button(
            path_frame,
            text='Browse',
            command=lambda: self.export.set(
                os.path.normpath(d) if (
                    d := askdirectory(
                        title='Choose export path',
                        initialdir=self.export.get()
                    )
                )
                else self.export.get()
            )
        ).grid(row=0, column=1,
               sticky='e')

        line_num += 1
        Label(
            frame,
            font=Font(size=7),
            text='Made by Leonid (https://github.com/G4m3-80ft)',
            fg='grey',
            justify='right'
        ).grid(row=line_num, column=1,
               columnspan=2,
               sticky='se')

        for i in range(line_num):
            frame.rowconfigure(i, weight=1)

    def scan_resolutions(self, *_) -> None:
        scan_path: str = self.scan_entry.get()

        if not os.access(scan_path, os.R_OK):
            showerror('Error', f'Can\'t read path for scan!')
            return None

        if not scan_path.endswith(os.sep):
            scan_path += os.sep

        self.scan_entry["state"] = 'readonly'
        export_path: str = scan_path + 'better-images'
        self.export.set(export_path)

        w: LoadingWindow = LoadingWindow('Scanning resolutions', size=20)

        for file in filter(lambda p: os.path.isfile(scan_path + p), os.listdir(scan_path)):
            filepath: str = scan_path + file

            try:
                im = Image.open(filepath)
            except PIL.UnidentifiedImageError:
                continue

            self.image_resolutions[file] = im.size

            w.step()
            self.root.update()
            self.root.update_idletasks()

        w.destroy()

        # noinspection PyTypeChecker
        min_res: int = min(map(min, self.image_resolutions.values()))
        self.se['state'] = 'normal'
        self.shrink.set(str(min_res))

        return None

    def scan_duplicates(self, *_) -> None:
        duplicate_images: list[list[str], ...] = [[]]

        scan_path: str = self.scan_entry.get()

        if not scan_path.endswith(os.sep):
            scan_path += os.sep

        if not self.shrink.get():
            # noinspection PyTypeChecker
            self.shrink.set(
                str(
                    min(
                        map(
                            min,
                            self.image_resolutions.values()
                        )
                    )
                )
            )
        res: int = int(self.shrink.get())
        self.se['state'] = 'readonly'

        size: int = (len(self.image_resolutions) ** 2 - len(self.image_resolutions)) // 2
        w: LoadingWindow = LoadingWindow('Scanning duplicates', size=size + 1, determinate=True)

        for i, path1 in enumerate(self.image_resolutions.keys(), start=1):
            im1: Image.Image = Image.open(scan_path + path1)
            w.current_task.set(f'Compressing 1st image №{i}...')
            self.root.update()
            im1.thumbnail((res,) * 2)

            for j, path2 in enumerate(tuple(self.image_resolutions)[i:], start=1):
                if path2 in chain.from_iterable(duplicate_images):
                    continue

                im2: Image.Image = Image.open(scan_path + path2)
                w.current_task.set(f'Compressing 2nd image №{i + j}...')
                self.root.update()
                im2.thumbnail((res,) * 2)

                w.current_task.set(f'Comparing sizes ({i} & {i + j})...')
                self.root.update()
                if im1.size == im2.size:
                    w.current_task.set(f'Comparing colors ({i} & {i + j})...')
                    self.root.update()
                    im = ImageChops.subtract(im1.convert('L'), im2.convert('L'))
                    im.thumbnail((1, 1))
                    if im.getpixel((0, 0)) == 0:
                        duplicate_images[-1].append(path2)

                w.step()
                self.root.update()
                self.root.update_idletasks()

            if duplicate_images[-1]:
                duplicate_images[-1].insert(0, path1)
                duplicate_images.append([])

        if not duplicate_images[-1]:
            duplicate_images.pop()

        images: Menu = Menu(
            self.mb,
            tearoff=False
        )

        group_paths: list[str]
        for group_paths in duplicate_images:
            group_paths.sort(key=lambda x: self.image_resolutions[x], reverse=True)
            sub_images: Menu = Menu(tearoff=False)
            for path in group_paths:
                check_var: IntVar = IntVar()
                size: tuple[int, int] = self.image_resolutions[path]

                if path == group_paths[0]:
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

            icon = Image.open(scan_path + group_paths[0])
            icon.thumbnail((50, 50))
            images.add_cascade(
                label=group_paths[0],
                image=PhotoImage(icon),
                compound='left',
                menu=sub_images
            )

            w.step()
            self.root.update()
            self.root.update_idletasks()

        w.destroy()
        showinfo(
            'Info',
            "Scanning is finished.\n"
            f"{len(tuple(j for i in duplicate_images for j in i))} duplicates found."
        )

        # TODO: Do sth with menu being larger than the screen
        self.mb["menu"] = images

    def export_selected(self, *_) -> None:
        scan_path: str = self.scan_entry.get()

        if not scan_path.endswith(os.sep):
            scan_path += os.sep

        export_path: str = self.export.get()

        if not export_path.endswith(os.sep):
            export_path += os.sep

        if export_path == scan_path:
            export_path += 'better-images'

        if not os.access(export_path, os.W_OK):
            # Slicing off os.sep: https://docs.python.org/3/library/os.path.html#os.path.basename
            if os.path.basename(export_path[:-1]) != 'better-images':
                showerror('Error', f'Can\'t access export path!')
                return None

            if not os.access(os.path.dirname(export_path[:-1]), os.W_OK):
                showerror('Error', f'Can\'t access export path!')
                return None

            os.mkdir(export_path)

        w: LoadingWindow = LoadingWindow('Exporting', size=len(self.selected), determinate=True)

        for path in self.selected:
            w.current_task.set(f'Exporting {path}...')
            shutil.copy2(scan_path + path, export_path)

            w.step()
            self.root.update()
            self.root.update_idletasks()

        w.destroy()
        showinfo('Info', 'Export finished!')


Root().root.mainloop()
