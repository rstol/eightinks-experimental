from galvani import BioLogic
import tkinter as tk
import pandas as pd
from tkinter import *
from tkinter import filedialog
from tkinter import ttk
from tkinter import messagebox
import pathlib
import os
import subprocess
import platform

root = tk.Tk()
s = ttk.Style()
root.title("MPR Converter")
root.geometry("600x480+100+100")
ttkstyle = ttk.Style(root)
ttkstyle.configure('lefttab.TNotebook', tabposition='nw')
my_notebook = ttk.Notebook(root, style='lefttab.TNotebook')
importtab = Frame(my_notebook, width=200, height=200, bg="grey")
my_notebook.add(importtab, text="Import and convert data")
my_notebook.pack(expand=True, fill="both")


def multiimport0():
    global text_list
    if not import_tree.get_children():
        pass
    else:
        import_tree.delete(*import_tree.get_children())
    text_files = filedialog.askopenfilenames()
    text_list = list(text_files)
    # print(text_list)
    names_list = []
    count = 0
    for record in text_list:
        path = pathlib.PurePath(record)
        import_tree.insert(parent='', index='end', iid=count,
                           text=path.name, values=record)
        names_list.append(path.name)
        count += 1


def export_toexcel():
    try:
        x = import_tree.selection()
        item_text = [import_tree.item(item_i, "values") for item_i in x]
        files_all = [BioLogic.MPRfile(file[0]) for file in item_text]
        df_all = [pd.DataFrame(files_all[i].data)
                  for i in range(len(files_all))]
        for i in range(len(df_all)):
            df_all[i].to_excel(item_text[i][0][:-4] + ".xlsx", index=False)
        # messagebox.showinfo("Export completed!", "Export to .xlsx file completed")
        popup()
    except ValueError:
        messagebox.showerror("Error", "Wrong file format :(")
    # except:
    #    messagebox.showerror("Error", "Oops, something went wrong :(")


def export_tocsv():
    try:
        x = import_tree.selection()
        item_text = [import_tree.item(item_i, "values") for item_i in x]
        files_all = [BioLogic.MPRfile(file[0]) for file in item_text]
        df_all = [pd.DataFrame(files_all[i].data)
                  for i in range(len(files_all))]
        for i in range(len(df_all)):
            df_all[i].to_csv(item_text[i][0][:-4] + ".csv", index=False)
        # messagebox.showinfo("Export completed!", "Export to .csv file completed")
        popup()
    except ValueError:
        messagebox.showerror("Error", "Wrong file format :(")
    # except:
    #    messagebox.showerror("Error", "Oops, something went wrong :(")


def export_totxt():
    try:
        x = import_tree.selection()
        item_text = [import_tree.item(item_i, "values") for item_i in x]
        files_all = [BioLogic.MPRfile(file[0]) for file in item_text]
        df_all = [pd.DataFrame(files_all[i].data)
                  for i in range(len(files_all))]
        # header= [df_all[i].columns for i in range(len(df_all))]
        # print(header[0])
        for i in range(len(df_all)):
            # np.savetxt(item_text[i][0][:-4] + ".txt", df_all[i].values, header=df_all[i].columns, delimiter='\t')
            df_all[i].to_csv(item_text[i][0][:-4] +
                             ".txt", index=False, sep='\t')
        # messagebox.showinfo("Export completed!", "Export to .txt file completed")
        popup()
    except ValueError:
        messagebox.showerror("Error", "Wrong file format :(")
    # except:
     #   messagebox.showerror("Error", "Oops, something went wrong :(")


def popup():
    pop = Toplevel(root)
    pop.title("Info")
    pop.geometry("300x140+130+400")
    pop_label = Label(pop, text="Export completed!", font=('helvetica', 12))
    pop_label.pack(pady=10)

    mframe = Frame(pop)
    mframe.pack(pady=5)

    ok_button = tk.Button(mframe, text="Close this window", command=pop.destroy, font=(
        'helvetica', 12, 'bold'), width=15)
    show_folder = tk.Button(mframe, text="Show folder",
                            command=openfile, font=('helvetica', 12), width=15)
    ok_button.grid(row=1, column=0, padx=5, pady=5)
    show_folder.grid(row=0, column=0, padx=5, pady=5)


def openfile():
    path = text_list[0]
    path = os.path.dirname(path)
    if platform.system() == 'Darwin':       # macOS
        subprocess.call(('open', path))
    elif platform.system() == 'Windows':    # Windows
        os.startfile(path)
    else:                                   # linux variants
        subprocess.call(('xdg-open', path))


fixframe = Frame(importtab)
info_frame = Frame(importtab)
imp_frame = Frame(fixframe)

info_text_label = Label(info_frame, font=(
    'arial', 12), text="Instructions:\n\n1. Import one or more .mpr files \n (No spaces in file name) \n\n2. Select one or more files in the left list.\n(Hold SHIFT or CTRL to select multiple files)\n\n3. Export selected files as new file formats")
info_text_label.pack()
import_tree = ttk.Treeview(imp_frame, selectmode='extended', show='tree')
vsbi = ttk.Scrollbar(imp_frame, orient='vertical', command=import_tree.yview)

vsbi.pack(side='right', fill='y')
import_tree.pack(side='left')
import_tree.configure(yscrollcommand=vsbi.set)
itemn = 0

browseButton = tk.Button(fixframe, text="Import .mpr files",
                         command=multiimport0, font=('helvetica', 12, 'bold'), width=15)
exportButton_xlsx = tk.Button(fixframe, text="Export as .xlsx file",
                              command=export_toexcel, font=('helvetica', 12, 'bold'), width=15)
exportButton_CSV = tk.Button(fixframe, text="Export as .csv file",
                             command=export_tocsv, font=('helvetica', 12, 'bold'), width=15)
exportButton_txt = tk.Button(fixframe, text="Export as .txt file",
                             command=export_totxt, font=('helvetica', 12, 'bold'), width=15)
browseButton.grid(row=0, column=0, padx=10, pady=10)
exportButton_CSV.grid(row=3, column=0, padx=10, pady=10)
exportButton_xlsx.grid(row=2, column=0, padx=10, pady=10)
exportButton_txt.grid(row=4, column=0, padx=10, pady=10)

fixframe.grid(row=0, column=0, padx=10, pady=10, sticky=N)
imp_frame.grid(row=1, column=0, padx=10, pady=10)

info_frame.grid(row=0, column=1, padx=10, pady=10, sticky=N)


root.mainloop()
