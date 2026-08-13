# coding=utf-8
from laotaoui import *
import tkinter as tk
import tkinter.ttk as ttk
import os, sys, win32api, win32con,re,json,winsound,webbrowser
from tkinter import filedialog
VERSION='1.0.0'
MITLICENSE="""MIT License

Copyright © 2026-2031 炸图监管者

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the “Software”), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE."""


def SetExpandedTreeviewRowColor(widget, color1=WIDGETBG, color2=TEXTBG, fore_color=TEXTFG):
    """
    为Treeview设置交替行颜色（仅针对可见/已展开的行）
    :param widget: Treeview实例
    :param color1: 奇数行背景色 (默认WIDGETBG)
    :param color2: 偶数行背景色 (默认TEXTBG)
    """
    # 1. 定义两个标签并配置颜色
    widget.tag_configure('odd_row', background=color1, foreground=fore_color)
    widget.tag_configure('even_row', background=color2, foreground=fore_color)
    
    # 2. 递归获取所有可见（已展开）的节点
    def get_visible_items(parent=''):
        items = []
        for child in widget.get_children(parent):
            items.append(child)
            # 只有当子节点展开时才递归获取
            if widget.item(child, 'open'):
                items.extend(get_visible_items(child))
        return items
    
    # 3. 获取所有可见节点
    visible_items = get_visible_items()
    
    # 4. 遍历所有可见节点，按视觉顺序分配标签
    for index, item in enumerate(visible_items):
        # index 为偶数 -> even_row, index 为奇数 -> odd_row
        tag = 'even_row' if index % 2 == 0 else 'odd_row'
        
        # 获取该节点原有的 tags (避免覆盖其他状态标签)
        current_tags = widget.item(item, 'tags')
        if isinstance(current_tags, str):
            current_tags = (current_tags,)
            
        # 移除旧的颜色标签 (防止重复调用时标签叠加)
        new_tags = [t for t in current_tags if t not in ('odd_row', 'even_row')]
        new_tags.append(tag)
        
        # 重新设置 tags
        widget.item(item, tags=tuple(new_tags))


class UndoManager:
    """撤销与重做管理器"""
    def __init__(self):
        self.undo_stack = []
        self.redo_stack = []

    def push(self, action_type, item_id, old_value, new_value):
        """记录操作"""
        self.undo_stack.append({
            'type': action_type,
            'id': item_id,
            'old': old_value,
            'new': new_value
        })
        # 新操作会清空重做栈
        self.redo_stack.clear()

    def can_undo(self):
        return len(self.undo_stack) > 0

    def can_redo(self):
        return len(self.redo_stack) > 0

    def pop_undo(self):
        return self.undo_stack.pop() if self.undo_stack else None

    def push_redo(self, action):
        self.redo_stack.append(action)

    def pop_redo(self):
        return self.redo_stack.pop() if self.redo_stack else None

    def clear(self):
        self.undo_stack.clear()
        self.redo_stack.clear()


class MCLangTools:
    def __init__(self):
      #  self.lang_entries = {}          # 完整数据：{完整键名: 值}
        self.updating_path = False      # 防止选择与筛选互相触发
        self.search_window = None
        self.undo_manager = UndoManager()  # 初始化撤销管理器
        self.LANG_EDITION=None
        self._middle_origin_y = 0
        self._middle_dragging = False
        self.is_modified=False
        self.path_nav_history = []          # 路径前进/后退栈（与 combobox 下拉历史无关）
        self.path_nav_index = -1           # 当前在路径导航栈中的位置
        self._suppress_path_nav_record = False  # 前进/后退时不写入导航栈
        LoadFont(f'{libresource}/WS_Segoe_MDL2_Assets-Regular.ttf')

    def update_title(self):
        """根据是否有未保存更改更新窗口标题"""
        base_title = '万岁™Minecraft多语言编辑器'
        if self.is_modified:
            self.root.title(f'*[未保存] {base_title}')
        else:
            self.root.title(base_title)

    def layout_window(self,):
        SetDPI()
        self.root = tk.Tk()
        self.update_title()
        self.update_title()
        width = 1500
        height = 900
        screenwidth = self.root.winfo_screenwidth()
        screenheight = self.root.winfo_screenheight()
        geometry = '%dx%d+%d+%d' % (width, height, (screenwidth - width) / 2, (screenheight - height-100) / 2)
        self.root.geometry(geometry)
        self.root.config(bd=0, highlightthickness=0, bg=WINDOWBG)
        self.root.protocol('WM_DELETE_WINDOW', self.close_root)
        self.root.focus()

        tk.Label(self.root, fg=TEXTFG, bg=WINDOWBG, text=f"V{VERSION}", anchor='e').place(x=1280, y=70, width=200, height=30)

        self.font_icon=tkfont.Font(family='WS_Segoe_MDL2_Assets',size=12)

        style_scrollbar = ttk.Style()
        style_scrollbar.configure("TScrollbar", background=WINDOWBG)

        tk.Label(self.root, fg=TEXTFG, bg=WINDOWBG, text='语言文件:', anchor='w').place(x=20, y=20, width=80, height=30)

        self.entry_file = DEntry(self.root,state='readonly')
        self.entry_file.place(x=100, y=20, width=1380, height=30)
        


        self.var_entry_path = tk.StringVar()
        self.combobox_path = DCombobutton(self.root,textvariable=self.var_entry_path,state='normal',close_list_command=self.on_path_committed)
        self.combobox_path.place(x=100, y=70, width=720, height=30)
        self.var_entry_path.trace_add("write", lambda *_: self.on_path_text_changed())
        self.combobox_path.Entry.bind('<Return>', self.on_path_return, add='+')

        BindTipWindow(self.combobox_path,text='浏览路径(按下回车确定)')


        self.frame_path_operation=tk.Frame(self.root,bg=TEXTBG)
        self.frame_path_operation.place(x=20,y=70,width=60,height=30)

        self.button_previous_path=DAlphaButton(self.frame_path_operation,text='',bg=WINDOWBG,font=self.font_icon,
                                        command=self.go_previous_path)
        self.button_previous_path.place(x=0,y=0,width=30,height=30)
        BindTipWindow(self.button_previous_path,text='上一个路径')

        self.button_next_path=DAlphaButton(self.frame_path_operation,text='',bg=WINDOWBG,font=self.font_icon,
                                        command=self.go_next_path)
        self.button_next_path.place(x=30,y=0,width=30,height=30)
        BindTipWindow(self.button_next_path,text='下一个路径')


        self.frame_file=tk.Frame(self.root,bg=TEXTBG)
        self.frame_file.place(x=20,y=120,width=180,height=30)

        self.button_file = DAlphaButton(self.frame_file,text='\uE8B7', 
                                        command=self.browse_lang_file_dialog,font=self.font_icon,bg=TEXTBG)
        self.button_file.place(x=0, y=0, width=30, height=30)
        BindTipWindow(self.button_file,text='打开(Ctrl+O)')
        self.root.bind('<Control-o>', self.browse_lang_file_dialog)

        
        self.button_save = DAlphaButton(self.frame_file, text='\uE105', 
                                        command=self.save_file,font=self.font_icon,bg=TEXTBG)
        self.button_save.place(x=40, y=0, width=30, height=30)
        BindTipWindow(self.button_save,text='保存(Ctrl+S)')
        self.root.bind('<Control-s>', self.save_file)

        self.button_save_as = DAlphaButton(self.frame_file, text='\uEA35', 
                                           command=self.save_as_lang_file,font=self.font_icon,bg=TEXTBG)
        self.button_save_as.place(x=70, y=0, width=30, height=30)
        BindTipWindow(self.button_save_as,text='另存为(Ctrl+Shift+S)')
        self.root.bind('<Control-Shift-s>', self.save_as_lang_file)
        self.root.bind('<Control-Shift-S>', self.save_as_lang_file)


        self.button_import = DAlphaButton(self.frame_file, text='\uE118', command=self.import_file,font=self.font_icon,bg=TEXTBG)
        self.button_import.place(x=110, y=0, width=30, height=30)
        BindTipWindow(self.button_import,text='导入(Ctrl+I)')
        self.root.bind('<Control-i>', self.import_file)



        self.button_output = DAlphaButton(self.frame_file, text='\uF714', 
                                           command=lambda:self.convert_tree_to_text(update_text=True),font=self.font_icon,bg=TEXTBG)
        self.button_output.place(x=150, y=0, width=30, height=30)
        BindTipWindow(self.button_output,text='完整输出(Ctrl+D)')
        self.root.bind('<Control-d>', lambda e:self.convert_tree_to_text(update_text=True))




        self.frame_edit_operation=tk.Frame(self.root,bg=TEXTBG)
        self.frame_edit_operation.place(x=220,y=120,width=60,height=30)

        self.button_undo = DAlphaButton(self.frame_edit_operation,text='\uE10E',
                                        command=self.undo,font=self.font_icon,bg=TEXTBG)
        self.button_undo.place(x=0,y=0,width=30,height=30)
        BindTipWindow(self.button_undo,text='撤销(Ctrl+Z)')
        self.root.bind('<Control-z>', self.undo)

        self.button_redo = DAlphaButton(self.frame_edit_operation,text='\uE10D',
                                        command=self.redo,font=self.font_icon,bg=TEXTBG)
        self.button_redo.place(x=30,y=0,width=30,height=30)
        BindTipWindow(self.button_redo,text='重做(Ctrl+Y)')
        self.root.bind('<Control-y>', self.redo)
        self.root.bind('<Control-Shift-Z>', self.redo)
        self.root.bind('<Control-Shift-z>', self.redo)




        self.frame_treeview_operation=tk.Frame(self.root,bg=TEXTBG)
        self.frame_treeview_operation.place(x=300,y=120,width=160,height=30)

        self.button_expand_selected = DAlphaButton(self.frame_treeview_operation,text='\uE972',
                                                   command=self.expand_selected,font=self.font_icon,bg=TEXTBG)
        self.button_expand_selected.place(x=0,y=0,width=30,height=30)
        BindTipWindow(self.button_expand_selected,text='展开所选(Ctrl+W)')
        self.root.bind('<Control-w>', self.expand_selected)

        self.button_collapse_selected = DAlphaButton(self.frame_treeview_operation,text='\uE971',
                                                     command=self.collapse_selected,font=self.font_icon,bg=TEXTBG)
        self.button_collapse_selected.place(x=30,y=0,width=30,height=30)
        BindTipWindow(self.button_collapse_selected,text='收起所选(Ctrl+E)')
        self.root.bind('<Control-e>', self.collapse_selected)
        
        self.button_auto_operate_selected = DAlphaButton(self.frame_treeview_operation,text='\uE174',
                                                     command=self.toggle_expand_selected,font=self.font_icon,bg=TEXTBG)
        self.button_auto_operate_selected.place(x=60,y=0,width=30,height=30)
        BindTipWindow(self.button_auto_operate_selected,text='快速展开/收起所选(Ctrl+Q)')
        self.root.bind('<Control-q>', self.toggle_expand_selected)

        self.button_expand_all = DAlphaButton(self.frame_treeview_operation,text='\uE169',
                                              command=self.expand_all,font=self.font_icon,bg=TEXTBG)
        self.button_expand_all.place(x=100,y=0,width=30,height=30)
        BindTipWindow(self.button_expand_all,text='展开全部(Alt+W)')
        self.root.bind('<Alt-w>', self.expand_all)

        self.button_collapse_all = DAlphaButton(self.frame_treeview_operation,text='\uE16A',
                                                command=self.collapse_all,font=self.font_icon,bg=TEXTBG)
        self.button_collapse_all.place(x=130,y=0,width=30,height=30)
        BindTipWindow(self.button_collapse_all,text='收起全部(Alt+E)')
        self.root.bind('<Alt-e>', self.collapse_all)



        self.frame_view=tk.Frame(self.root,bg=TEXTBG)
        self.frame_view.place(x=480,y=120,width=60,height=30)

        self.button_search = DAlphaButton(self.frame_view, text='\uE71E', 
                                          command=self.open_search_window,font=self.font_icon,bg=TEXTBG)
        self.button_search.place(x=0, y=0, width=30, height=30)
        BindTipWindow(self.button_search,text='搜索(Ctrl+F) & 替换(Ctrl+H)')
        self.root.bind('<Control-f>', self.open_search_window)
        self.root.bind('<Control-h>', lambda e:self.open_search_window(replace=True))

        self.button_goto = DAlphaButton(self.frame_view, text='\uE182', 
                                           command=self.goto,font=self.font_icon,bg=TEXTBG)
        self.button_goto.place(x=30, y=0, width=30, height=30)
        BindTipWindow(self.button_goto,text='跳转到所选(Ctrl+R)')
        self.root.bind('<Control-r>', self.goto)


        self.frame_software=tk.Frame(self.root,bg=TEXTBG)
        self.frame_software.place(x=560,y=120,width=60,height=30)

        self.button_help= DAlphaButton(self.frame_software, text='\uE9CE', 
                                           command=self.help,font=self.font_icon,bg=TEXTBG)
        self.button_help.place(x=0, y=0, width=30, height=30)
        BindTipWindow(self.button_help,text='帮助')

        self.button_about= DAlphaButton(self.frame_software, text='\uE946', 
                                           command=self.about,font=self.font_icon,bg=TEXTBG)
        self.button_about.place(x=30, y=0, width=30, height=30)
        BindTipWindow(self.button_about,text='关于')


        self.button_reset_all = DButton(self.root,text='\uE777', command=self.do_reset_all,
                                             fg=REDTEXTFG,font=self.font_icon,)
        self.button_reset_all.place(x=1450, y=120, width=30, height=30)
        BindTipWindow(self.button_reset_all,text='重置',text_color=REDTEXTFG)


        def update_auto_wrap():
            if self.var_checkbutton_auto_wrap.get():
                self.text_lang.config(wrap='word')
            else:
                self.text_lang.config(wrap='none')

        self.var_checkbutton_auto_wrap=tk.BooleanVar()
        self.var_checkbutton_auto_wrap.set(False)
        self.checkbutton_auto_wrap=tk.Checkbutton(self.search_window,text='自动换行',onvalue=True, offvalue=False, anchor='w',variable=self.var_checkbutton_auto_wrap,
                                bg=WINDOWBG,fg=TEXTFG,activebackground=WINDOWBG,activeforeground=TEXTFG,selectcolor=WIDGETBG,)
        self.checkbutton_auto_wrap.place(x=860,y=120,width=100,height=30)
        #BindTipWindow(self.checkbutton_auto_wrap,text='自动换行')
        #事件绑定在最下面


        def update_auto_goto():
            if self.var_checkbutton_auto_goto.get():
                self.text_lang.bind('<Triple-Button-1>',lambda e:self.root.after_idle(self.goto))
            else:
                self.text_lang.unbind_all('<Triple-Button-1>',)

        self.var_checkbutton_auto_goto=tk.BooleanVar()
        self.checkbutton_auto_goto=tk.Checkbutton(self.search_window,text='三击跳转',onvalue=True, offvalue=False, anchor='w',variable=self.var_checkbutton_auto_goto,
                                bg=WINDOWBG,fg=TEXTFG,activebackground=WINDOWBG,activeforeground=TEXTFG,selectcolor=WIDGETBG)
        self.checkbutton_auto_goto.place(x=980,y=120,width=100,height=30)
        BindTipWindow(self.checkbutton_auto_goto,text='快速点击文本框三次,自动跳转到点击的行的树状图位置.')
        #绑定在最底下


        style = ttk.Style()
        style.theme_use("alt")
        style.configure("Treeview", rowheight=25,fieldbackground=WINDOWBG,background=WINDOWBG,
                        foregroung=TEXTFG,borderwidth=0,highlightthickness=0) # 填充背景色
   
        style.configure("Treeview.Heading",
                        background=WINDOWBG,      # 表头背景色（蓝色）
                        foreground=TEXTFG,        # 表头文字颜色（白色）
                        borderwidth=0,
                        highlightthickness=0,)          # 扁平化边框
        # 3. 关键步骤：锁死动态样式（防止鼠标悬停或点击时变回系统默认的灰色）
        style.map("Treeview.Heading",
                background=[('active', WIDGETBG),  # 鼠标悬停时的深蓝色
                            ('pressed', WINDOWBG)], # 鼠标点击时的更深蓝色
                foreground=[('active', TEXTFG),
                            ('pressed', TEXTFG)],
                borderwidth=[('active', 0), ('pressed', 0)],    
                highlightthickness=[('active', 0), ('pressed', 0)],   )
        # 配置被选中时的颜色
        style.map("Treeview",
                background=[('selected', AlphaBlend(WINDOWBG,HIGHLIGHT,0.5))],
                foreground=[('selected',TEXTFG )],
                borderwidth=[('active', 0), ('pressed', 0)],    # 外边框宽度设为 0
                highlightthickness=[('active', 0), ('pressed', 0)],)    # 高亮边框宽度设为 0

        self.scrollbar_treeview_y = tk.Scrollbar(self.root,bg=WINDOWBG)
        self.scrollbar_treeview_y.place(x=820, y=170, width=20, height=710)
        self.treeview_lang = ttk.Treeview(self.root, show="tree headings", columns=["value"],takefocus=True,
                                          selectmode='browse', yscrollcommand=self.scrollbar_treeview_y.set)
        self.treeview_lang.place(x=20, y=170, width=800, height=710)
        self.scrollbar_treeview_y.config(command=self.treeview_lang.yview)

        self.treeview_lang.heading("#0", text="键", anchor='center')
        self.treeview_lang.heading("value", text="值", anchor='center')
        self.treeview_lang.column("#0", width=300, anchor='w')
        self.treeview_lang.column("value", width=490, anchor='w')

        self.treeview_lang.bind("<Double-Button-1>", self.on_double_click)
        self.treeview_lang.bind("<Return>", self.on_double_click)
        self.treeview_lang.bind('<F2>', self.on_double_click)

        # 绑定选择与变更事件（统一到同一个刷新函数）
        self.treeview_lang.bind('<<TreeviewSelect>>', self.update_text_content)
        self.treeview_lang.bind('<<TreeviewEvent>>', self.update_text_content)
        # 在 layout_window 方法中，找到创建 treeview_lang 的部分后添加：
        self.treeview_lang.bind('<<TreeviewOpen>>', self.treeview_open_or_close)
        self.treeview_lang.bind('<<TreeviewClose>>', self.treeview_open_or_close)
        # 【新增】绑定右键点击事件，用于在"键"列生成只读复制框
        self.treeview_lang.bind("<Button-3>", self.on_right_click_key)
        self.treeview_lang.bind("<Button-2>", self._on_middle_press)
        self.treeview_lang.bind("<ButtonRelease-2>", self._on_middle_release)

        


        self.text_lang = tk.Text(self.root,
                          bg=TEXTBG, fg=TEXTFG, selectbackground=HIGHLIGHT, selectforeground=TEXTFG,
                          insertbackground=HIGHLIGHT, insertontime=500, insertofftime=500, insertwidth=2,
                          font='consolas 12', bd=1, relief='solid', wrap='none', undo=True, state='disabled',)

        self.text_lang.place(x=860, y=170, width=600, height=690)

        self.scrollbar_text_y = tk.Scrollbar(self.root, command=self.text_lang.yview,bg=WINDOWBG)
        self.scrollbar_text_y.place(x=1460 , y=170, width=20, height=710)
        
        self.scrollbar_text_x = tk.Scrollbar(self.root, orient='horizontal', command=self.text_lang.xview,bg=WINDOWBG)
        self.scrollbar_text_x.place(x=860, y=860, width=600, height=20)

        self.text_lang.config(yscrollcommand=self.scrollbar_text_y.set, xscrollcommand=self.scrollbar_text_x.set)
        
        def increase_font_size(event):
            f = tkfont.Font(font=self.text_lang.cget("font"))
            f.configure(size=f.actual("size") + 1)
            self.text_lang.configure(font=f)
        def decrease_font_size(event):
            f = tkfont.Font(font=self.text_lang.cget("font"))
            new_size = max(1, f.actual("size") - 1)  # 防止变成 0 或负数
            f.configure(size=new_size)
            self.text_lang.configure(font=f)
        def adjust_font_size(event):
            # event.delta > 0 代表向上滚动（放大），否则向下滚动（缩小）
            change = 1 if event.delta > 0 else -1
            f = tkfont.Font(font=self.text_lang.cget("font"))
            new_size = max(1, f.actual("size") + change)
            f.configure(size=new_size)
            self.text_lang.configure(font=f)
        self.root.bind("<Control-minus>", decrease_font_size)
        self.root.bind("<Control-KP_Subtract>", decrease_font_size)
        self.root.bind("<Control-plus>", increase_font_size)
        self.root.bind("<Control-KP_Add>", increase_font_size)
        self.text_lang.bind("<Control-MouseWheel>", adjust_font_size)

        self.var_checkbutton_auto_wrap.trace_add('write',lambda *_:update_auto_wrap())
        self.var_checkbutton_auto_goto.trace_add('write',lambda *_:update_auto_goto())
        self.var_checkbutton_auto_goto.set(True)
        

        self.root.bind('<F1>', self.help)

    def treeview_open_or_close(self,event=None,):
        winsound.PlaySound(f"{libresource}navigate.wav", winsound.SND_FILENAME | winsound.SND_ASYNC)
        self.root.after_idle( lambda: SetExpandedTreeviewRowColor(self.treeview_lang))

    def undo(self, event=None):
        """执行撤销操作"""
        action = self.undo_manager.pop_undo()
        if not action:
            return "break"
        
        # 撤销编辑：将值恢复为 old
        if action['type'] == 'edit':
            if self.treeview_lang.exists(action['id']):
                self.treeview_lang.item(action['id'], values=(action['old'],))
                self.treeview_lang.selection_set(action['id'])
                self.treeview_lang.focus(action['id'])
                self.treeview_lang.see(action['id'])
                self.update_text_content()
            # 将动作压入重做栈
            self.undo_manager.push_redo(action)
            
        return "break"  # 阻止事件继续传播

    def redo(self, event=None):
        """执行重做操作"""
        action = self.undo_manager.pop_redo()
        if not action:
            return "break"
            
        # 重做编辑：将值恢复为 new
        if action['type'] == 'edit':
            if self.treeview_lang.exists(action['id']):
                self.treeview_lang.item(action['id'], values=(action['new'],))
                self.treeview_lang.selection_set(action['id'])
                self.treeview_lang.focus(action['id'])
                self.treeview_lang.see(action['id'])
                self.update_text_content()
            # 将动作压回撤销栈
            self.undo_manager.undo_stack.append(action)
            
        return "break"

    def goto(self, event=None):
        """
        从右侧 Text 选中内容跳转。
        视为完整路径（可含 key=value，只取 = 前的键）。
        成功则填入路径框、写入历史并跳转。
        """
        try:
            selected = self.text_lang.get(tk.SEL_FIRST, tk.SEL_LAST)
        except tk.TclError:
            win32api.MessageBeep()
            return

        path = selected.split('\n', 1)[0].strip()
        if '=' in path:
            path = path.split('=', 1)[0].strip()
        path = path.rstrip('.').strip()

        if not path:
            win32api.MessageBeep()
            return

        if not self.treeview_lang.exists(path):
            win32api.MessageBeep()
            MessageBoxModern(
                parent=self.root,
                title='错误',
                text_blod='跳转失败',
                text=f'路径"{path}"在树状图中不存在.',
                icon='error',
                )
            return

        winsound.PlaySound(f"{libresource}navigate.wav", winsound.SND_FILENAME | winsound.SND_ASYNC)
        # 用户主动跳转：写入历史
        self.set_path_from_selection(path)   # 先同步显示
        self.add_path_to_history(path)
        self.navigate_to_exact_path(path)

    def import_file(self, event=None):
        """
        导入语言文件并合并到当前树。
        对已存在的键弹出一次询问：覆盖 / 跳过。
        """
        if self.LANG_EDITION==None:
            win32api.MessageBeep()
            return
        filetypes = [
            ("基岩版语言文件", "*.lang"),
            ("Java版语言文件", "*.json"),
            ("文本文档", "*.txt"),
            ("所有文件", "*.*"),
        ]
        file_path = filedialog.askopenfilename(
            parent=self.root,
            initialdir=os.getcwd(),
            title="导入",
            filetypes=filetypes,
        )
        if not file_path:
            return

        ext = os.path.splitext(file_path)[1].lower()
        if ext == '.json':
            import_edition = 'java'
        elif ext == '.lang':
            import_edition = 'bedrock'
        else:
            lang_version_bool = MessageBoxModern(
                parent=self.root,
                text='选择.lang(基岩版语言文件)或.json(Java版语言文件)文件.',
                title='选择',
                icon='question',
                text_blod='选择语言版本',
                text_true='基岩版',
                text_false='Java版',
                button_mode=2,
            )
            if lang_version_bool in [None, '']:
                return
            import_edition = 'bedrock' if lang_version_bool else 'java'

        # 读取并解析为 {完整键: 值}
        try:
            with open(file_path, 'r', encoding='utf8') as f:
                raw = f.read()
            entries = {}
            if import_edition == 'java':
                lang_dict = json.loads(raw)
                for key, value in lang_dict.items():
                    entries[str(key).strip()] = str(value)
            else:
                for line in raw.strip().split('\n'):
                    line = line.strip()
                    if not line or line.startswith('##') or '=' not in line:
                        continue
                    eq_idx = line.index('=')
                    key = line[:eq_idx].strip()
                    value = line[eq_idx + 1:].strip()
                    if '##' in value:
                        value = value.split('##')[0].strip()
                    if key:
                        entries[key] = value
        except Exception as e:
            MessageBoxModern(
                parent=self.root,
                text=e,
                title='错误',
                icon='error',
                text_blod='读取或解析导入文件失败',
            )
            return

        if not entries:
            MessageBoxModern(
                parent=self.root,
                text='文件中没有可导入的键值对.',
                title='导入',
                icon='info',
                text_blod='无内容可导入',
            )
            return

        # 是否存在需要决策的冲突键（树中已有同名节点）
        conflict_keys = [k for k in entries if self.treeview_lang.exists(k)]
        overwrite = True
        if conflict_keys:
            choice = MessageBoxModern(
                parent=self.root,
                text=f'导入文件中有{len(conflict_keys)}个键在表格中已存在,请选择对已存在键的处理方式.',
                title='导入',
                icon='question',
                text_blod='覆盖还是跳过已存在的键?',
                text_true='覆盖',
                text_false='跳过',
                button_mode=2,
                default_focus=1,
            )
            if choice in [None, '']:
                return
            overwrite = bool(choice)  # True=覆盖, False=跳过

        def ensure_path_and_set(key, value, do_overwrite):
            """确保键路径上的节点存在；叶子按策略写入值。返回是否发生了写入。"""
            parts = key.split('.')
            parent_iid = ''
            changed = False
            for i, part in enumerate(parts):
                current_iid = '.'.join(parts[:i + 1])
                is_leaf = (i == len(parts) - 1)
                if self.treeview_lang.exists(current_iid):
                    if is_leaf:
                        old_vals = self.treeview_lang.item(current_iid, 'values')
                        old_value = old_vals[0] if old_vals else ''
                        if do_overwrite:
                            if old_value != value:
                                self.treeview_lang.item(current_iid, values=(value,))
                                self.undo_manager.push('edit', current_iid, old_value, value)
                                changed = True
                        # 跳过：不动
                    # 非叶子已存在：无需处理
                else:
                    if is_leaf:
                        self.treeview_lang.insert(
                            parent_iid, tk.END, iid=current_iid,
                            text=part, values=(value,), open=False
                        )
                        self.undo_manager.push('edit', current_iid, '', value)
                        changed = True
                    else:
                        self.treeview_lang.insert(
                            parent_iid, tk.END, iid=current_iid,
                            text=part, values=('',), open=False
                        )
                parent_iid = current_iid
            return changed

        added = 0
        updated = 0
        skipped = 0
        for key, value in entries.items():
            exists = self.treeview_lang.exists(key)
            if exists and not overwrite:
                # 已存在且选择跳过：仍确保父路径（一般已存在），不改值
                skipped += 1
                continue
            before_vals = None
            if exists:
                before_vals = self.treeview_lang.item(key, 'values')
                before_vals = before_vals[0] if before_vals else ''
            wrote = ensure_path_and_set(key, value, do_overwrite=True if not exists else overwrite)
            if not exists:
                if wrote:
                    added += 1
            else:
                after_vals = self.treeview_lang.item(key, 'values')
                after_vals = after_vals[0] if after_vals else ''
                if before_vals != after_vals:
                    updated += 1
                else:
                    skipped += 1

        if self.LANG_EDITION is None:
            self.LANG_EDITION = import_edition

        self.sort_tree_by_custom_order()
        SetExpandedTreeviewRowColor(self.treeview_lang)
        if added or updated:
            self.is_modified = True
            self.update_title()

        MessageBoxModern(
            parent=self.root,
            title='导入',
            text_blod=f'成功导入 {added+updated} 项内容',
            text=f'新增 {added} 项;\n覆盖 {updated} 项;\n跳过 {skipped} 项.',
            icon='correct',)



    def close_root(self,):
        self.root.focus()
        if not self.is_modified:
            self.root.destroy()
            sys.exit()
        elif self.LANG_EDITION==None:
            self.root.destroy()
            sys.exit()
        elif MessageBoxModern(parent=self.root,text='未保存的更改将被丢弃,请及时保存.',title='疑问',text_blod='放弃所做的更改并退出?',icon='question',button_mode=2,text_true='退出',)==True :
            self.root.destroy()
            sys.exit()

    def save_file(self, event=None):
        """保存文件到原路径"""
        if self.LANG_EDITION is None:
            win32api.MessageBeep()
            return
        
        file_path = self.entry_file.get()
        if not file_path:
            win32api.MessageBeep()
            return

        def _write_file():
            try:
                content = self.convert_tree_to_text()
                if self.LANG_EDITION == 'java':
                    content = self.convert_bedrock_to_java(content)
                with open(file_path, 'w', encoding='utf8') as f:
                    f.write(content)
                self.is_modified = False
                self.update_title()
                self.button_save.config(text='\uE081')
                self.root.after(500,lambda:self.button_save.config(text='\uE105'))
            except Exception as e:
                MessageBoxModern(self.root, title='错误', text=e, text_blod='保存文件失败', icon='error',)

        self.root.after_idle(_write_file)

    def save_as_lang_file(self,event=None):
        if  self.LANG_EDITION==None:
            win32api.MessageBeep()
            return
        lang_version_bool=MessageBoxModern(parent=self.root, text='另存为.lang(基岩版语言文件)或.json(Java版语言文件)文件.', title='另存为', icon='question', text_blod='选择另存为的版本',text_true='基岩版',text_false='Java版',button_mode=2,default_focus=1 if self.LANG_EDITION=='bedrock' else 2)
        if lang_version_bool==None:
            return
        elif lang_version_bool==True:
            save_path=filedialog.asksaveasfilename(parent=self.root,title='另存为基岩版语言文件',initialfile=f"edited_{os.path.splitext(os.path.basename(self.entry_file.get()))[0]}.lang",filetypes=[('基岩版语言文件','*.lang'),("文本文档", "*.txt"), ("所有文件", "*.*")])
            if save_path:
                try:
                    bedrock_lang_text=self.convert_tree_to_text()
                    with open(save_path,'w',encoding='utf8') as f:
                        f.write(bedrock_lang_text)
                    # 另存为成功后：切换到新文件路径，清除修改标记，更新标题（等同于重新打开该文件）
                    self.entry_file.config(state='normal')
                    self.entry_file.delete(0, 'end')
                    self.entry_file.insert(0, save_path)
                    self.entry_file.config(state='readonly')
                    self.LANG_EDITION = 'bedrock'
                    self.is_modified = False
                    self.update_title()
                    MessageBoxModern(self.root,title='成功',text=rf'基岩版语言文件已另存为至: {save_path}',text_blod='另存为基岩版语言文件成功',icon='correct',)
                    self.button_save.config(text='\uE081')
                    self.root.after(500,lambda:self.button_save.config(text='\uE105'))
                except Exception as e:
                    MessageBoxModern(self.root,title='错误',text=e,text_blod='另存为基岩版语言文件失败',icon='error',)

        elif lang_version_bool==False:
            save_path=filedialog.asksaveasfilename(parent=self.root,title='另存为Java版语言文件',initialfile=f"edited_{os.path.splitext(os.path.basename(self.entry_file.get()))[0]}.json",filetypes=[('Java版语言文件','*.json'),("文本文档", "*.txt"), ("所有文件", "*.*")])
            if save_path:
                try:
                    with open(save_path,'w',encoding='utf8') as f:
                        f.write(self.convert_bedrock_to_java(self.convert_tree_to_text()))
                    # 另存为成功后：切换到新文件路径，清除修改标记，更新标题（等同于重新打开该文件）
                    self.entry_file.config(state='normal')
                    self.entry_file.delete(0, 'end')
                    self.entry_file.insert(0, save_path)
                    self.entry_file.config(state='readonly')
                    self.LANG_EDITION = 'java'
                    self.is_modified = False
                    self.update_title()
                    MessageBoxModern(self.root,title='成功',text=rf'Java版语言文件已另存为至: {save_path}',text_blod='另存为Java版语言文件成功',icon='correct',)
                except Exception as e:
                    MessageBoxModern(self.root,title='错误',text=e,text_blod='另存为Java版语言文件失败',icon='error',)

    def convert_bedrock_to_java(self, text_variable):
        """
        将基岩版语言文本转换为 Java 版 JSON 语言文本。
        规则：只以第一个 '=' 分割键和值，后面的所有内容（包括额外的 '='）都作为值。
        示例：key==  →  {"key":"="}
        忽略空行和以 ## 开头的注释行；值中 ## 之后的内容视为注释并丢弃。
        """
        lang_dict = {}
        lines = text_variable.strip().split('\n')

        for line in lines:
            line = line.strip()
            if not line or line.startswith('##'):
                continue
            if '=' not in line:
                continue

            # 只以第一个 = 分割
            eq_idx = line.index('=')
            key = line[:eq_idx].strip()
            value = line[eq_idx + 1:].strip()

            # 清理值中可能混入的注释
            if '##' in value:
                value = value.split('##')[0].strip()

            lang_dict[key] = value

        # 生成标准 JSON（保持插入顺序，不转义非 ASCII 字符）
        return json.dumps(lang_dict, ensure_ascii=False, indent=2)
    
    def browse_lang_file_dialog(self,event=None):
        if self.LANG_EDITION!=None:
            if MessageBoxModern(parent=self.root,text='未保存的更改将被丢弃,然后软件界面将会重置.',
                        title='警告',text_blod='放弃所做的更改并打开新文件?',icon='warning',
                        button_mode=2,default_focus=2,)!=True:
                return


        #打开文件选择对话框，用于选择 .lang 或 .txt 文件
        # 定义文件类型过滤器
        filetypes = [
            ("基岩版语言文件", "*.lang"),          # 只显示 .lang 文件
            ("Java版语言文件", "*.json"),          # 只显示 .lang 文件
            ("文本文档", "*.txt"),          # 只显示 .txt 文件
            ("所有文件", "*.*")            # 显示所有文件
        ]
        
        # 打开文件选择对话框
        # parent=root 指定对话框的父窗口，使其模态化
        # initialdir 可选，设置初始打开的目录
        # title 可选，设置对话框标题
        # filetypes 设置文件类型过滤器
        file_path = filedialog.askopenfilename(
            parent=self.root,
            initialdir=os.getcwd(),  # 默认打开当前工作目录
            title="打开",
            filetypes=filetypes,
            
        )
        if file_path in ['',None]:
            return
        if os.path.splitext(file_path)[1].lower() not in['.lang','.json']:
            lang_version_bool=MessageBoxModern(parent=self.root, text='选择.lang(基岩版语言文件)或.json(Java版语言文件)文件.', title='选择', icon='question', text_blod='选择语言版本',text_true='基岩版',text_false='Java版',button_mode=2,)
            if lang_version_bool in [None,'']:
                return
            self.LANG_EDITION = 'bedrock' if lang_version_bool else 'java'
        elif os.path.splitext(file_path)[1].lower() == '.json':
            self.LANG_EDITION = 'java'
        else:
            self.LANG_EDITION = 'bedrock'

            
        # 如果用户选择了文件，更新 entry_file 的内容
        if file_path and self.LANG_EDITION=='bedrock':
            try:
                self.reset_all()
                self.entry_file.config(state='normal',)
                self.entry_file.insert(0, file_path)  # 插入新选择的文件路径
                self.entry_file.config(state='readonly',)
                self.root.update()#立刻显示,减少焦虑
                with open(file_path, 'r', encoding='utf8') as f:
                    self.parse_lang_text_bedrock(f.read())
            except Exception as e:
                MessageBoxModern(parent=self.root, text=e, title='错误', icon='error', text_blod='解析基岩版语言文件失败',)

            
        elif file_path and self.LANG_EDITION=='java':
            try:
                self.reset_all()
                self.entry_file.config(state='normal',)
                self.entry_file.insert(0, file_path)  # 插入新选择的文件路径
                self.entry_file.config(state='readonly',)
                self.root.update()#立刻显示,减少焦虑
                with open(file_path, 'r', encoding='utf8') as f:
                    self.parse_lang_text_java(f.read())
            except Exception as e:
                MessageBoxModern(parent=self.root, text=e, title='错误', icon='error', text_blod='解析Java版语言文件失败',)
        else:
            MessageBoxModern(parent=self.root, text='无法解析此种未知版本的语言文件.', title='错误', icon='error', text_blod='未知的文件版本',)

    def run_app(self,):
        self.layout_window()
        self.root.update()
        ConvertPlaceToRelative(self.root)
        SetDarkTitleBar(self.root)
        self.root.iconbitmap(f"{libresource}mclangtool.ico")
        self.root.mainloop()
   
    def parse_lang_text_bedrock(self, text_variable):
        """
        解析 基岩版 文本变量并构建树形结构
        """
        # 清空现有表格内容
        for item in self.treeview_lang.get_children():
            self.treeview_lang.delete(item)

        # 获取文本内容并按行分割
        lines = text_variable.strip().split('\n')
        
        # 用于记录已经创建过的节点，避免重复创建
        existing_nodes = {"": ""} # 空字符串代表虚拟根节点

        for line in lines:
            line = line.strip()
            if not line or line.startswith('##'):
                continue # 忽略空行和注释行
            
            # 以第一个等号分割
            if '=' not in line:
                continue
                
            eq_idx = line.index('=')
            key = line[:eq_idx].strip()
            value = line[eq_idx+1:].strip()
            
            # 清理值中可能混入的注释 (如：文本 ##注释)
            # 注意：MC语言中有时值本身包含#，但通常 ### 是开发者注释的标志
            if '##' in value:
                value = value.split('##')[0].strip()
            # 按 '.' 分割键名
            parts = key.split('.')
            parent_iid = "" # 虚拟根节点
            for i, part in enumerate(parts):
                # 构建当前节点的完整路径作为 iid (保证唯一性，且能识别父子关系)
                current_iid = ".".join(parts[:i+1])
                
                # 如果这个节点还没创建过，则创建它
                if current_iid not in existing_nodes:
                    # 判断是否是叶子节点（最后一段）
                    if i == len(parts) - 1:
                        # 叶子节点：显示当前段名称，并赋值
                        self.treeview_lang.insert(parent_iid, tk.END, iid=current_iid, text=part, values=(value,), open=False)
                    else:
                        # 父级节点：只显示当前段名称，没有值
                        self.treeview_lang.insert(parent_iid, tk.END, iid=current_iid, text=part, values=("",), open=False)
                    existing_nodes[current_iid] = True
                # 当前节点作为下一级的父节点
                parent_iid = current_iid

        self.sort_tree_by_custom_order()
        self.convert_tree_to_text()

    def parse_lang_text_java(self, text_variable):
        """解析 JAVA版 语言文件"""
        lang_dict=json.loads(text_variable)
        bedrock_edition_lang_text=''
        for key,value in lang_dict.items():
            bedrock_edition_lang_text+=f'{key}={value}\n'
        self.parse_lang_text_bedrock(bedrock_edition_lang_text)

    def navigate_to_path(self, event=None):
        """
        处理combobox_path的导航功能
        - 当输入路径时，检查路径是否存在，改变背景色
        - 当按下回车且路径存在时，执行跳转，并将路径添加到历史记录头部
        """
        input_text = self.var_entry_path.get().rstrip('.').strip()
        if not input_text:
            # 清空输入时，恢复默认背景
            self.combobox_path.config(bg=WIDGETBG)
            return
        
        # 检查路径是否存在
        item_exists = self.treeview_lang.exists(input_text)
        
        if item_exists:
            # 路径存在，显示绿色背景
            self.combobox_path.config(bg=AlphaBlend(GREENLIGHT, WIDGETBG, 0.2))
            
            # 检查是否按下回车键
            if event and event.keysym == 'Return':
                # 1. 执行跳转
                self.navigate_to_exact_path(input_text)
                
                # 2. 将这一项添加到 combobox_path 的 values 历史记录中
                self.add_path_to_history(input_text)
        else:
            # 路径不存在，恢复默认背景
            self.combobox_path.config(bg=WIDGETBG)

    def get_all_items(self, parent=''):
        """
        获取树中所有节点（包括未展开的）
        """
        items = []
        for child in self.treeview_lang.get_children(parent):
            items.append(child)
            items.extend(self.get_all_items(child))
        return items

    def on_double_click(self, event):
        ''' 双击/回车事件处理：在值列创建编辑框'''
        # 1. 获取当前选中的行（支持键盘和鼠标）
        row_id = event.widget.focus()
        if not row_id:
            return

        # 2. 判断点击/触发的是哪一列
        # 对于键盘事件(如Return)，没有x坐标，默认视为操作值列(#1)
        if hasattr(event, 'x') and event.x > 0:
            column = event.widget.identify_column(event.x)
        else:
            column = '#1'  # 键盘触发时默认为值列

        # 如果点击的是左列 (#0) 或者无效区域，直接返回。
        # 直接返回意味着不返回 "break"，因此 Treeview 会保留默认行为（折叠/展开）。
        if column != '#1':
            return

        # 获取该节点的值
        item_values = event.widget.item(row_id, 'values')
        current_value = item_values[0] if item_values else ""

        # 如果值为空（父节点），允许双击值列进行展开/折叠，
        # 不返回 "break"，让 Treeview 执行默认行为。
        if not current_value:
            return

        # 获取单元格的精确位置和尺寸
        bbox = event.widget.bbox(row_id, column)
        if not bbox:
            return "break"
        x, y, width, height = bbox

        # 创建 DEntry 编辑控件
        entry_edit = DEntry(event.widget)
        entry_edit.insert('end', current_value)
        # 将光标移到最后
        entry_edit.icursor('end')

        # 保存原始值，用于取消时恢复
        entry_edit.original_value = current_value
        entry_edit.row_id = row_id
        entry_edit.tree_widget = event.widget

        def apply_edit(event=None):
            self.treeview_lang.unbind_all("<MouseWheel>")
            self.scrollbar_treeview_y.unbind('<B1-Motion>')
            self.scrollbar_treeview_y.unbind("<MouseWheel>")
            try:
                entry_edit.unbind_all("<FocusOut>")
                entry_edit.config(state='readonly')
            except Exception:
                return
            self.root.update()
            new_value = entry_edit.get()
            tree = entry_edit.tree_widget
            rid = entry_edit.row_id
            if new_value.replace(' ', '').replace('\t', '') == '':
                entry_edit.destroy()
                MessageBoxModern(
                    parent=self.root,
                    title='错误',
                    text_blod='文本不能为空',
                    text='如果文本为空或只有空格,则程序会标记此项为不可编辑项.',
                    icon='error',
                    
                )
            else:
                # 【修改点】只有当值确实发生改变时，才更新树并记录撤销操作
                if new_value != entry_edit.original_value:
                    tree.item(rid, values=(new_value,))
                    # 记录撤销操作
                    self.undo_manager.push('edit', rid, entry_edit.original_value, new_value)
                    self.is_modified = True
                    self.update_title()
                entry_edit.destroy()
            self.update_text_content()
            tree.focus_set()

        def cancel_edit(event=None):
            entry_edit.destroy()
            entry_edit.tree_widget.focus_set()

        entry_edit.place(x=x, y=y, width=width, height=height)
        entry_edit.bind("<Return>", apply_edit)
        entry_edit.bind("<Escape>", cancel_edit)
        entry_edit.bind("<FocusOut>", apply_edit)
        self.treeview_lang.bind("<MouseWheel>", apply_edit)
        self.scrollbar_treeview_y.bind('<B1-Motion>', apply_edit)
        self.scrollbar_treeview_y.bind("<MouseWheel>", apply_edit)
        entry_edit.focus_set()
        entry_edit.select_range(0, tk.END)

        return "break"

    def on_right_click_key(self, event):
        """右键点击'键'列时，生成只读DEntry以便复制"""
        row_id = event.widget.identify_row(event.y)
        column = event.widget.identify_column(event.x)

        # 仅当右键点击的是"键"列(#0)且有效行时触发
        if not row_id or column != '#0':
            return

        # 获取该节点的键名文本
        key_text = event.widget.item(row_id, 'text')
        if not key_text:
            return

        # 获取单元格位置
        bbox = event.widget.bbox(row_id, column)
        if not bbox:
            return "break"
        x, y, width, height = bbox

        # 【优化】计算文本实际宽度，让输入框刚好覆盖文字，避免覆盖整列导致遮挡展开箭头
        try:
            font = tkfont.Font(event.widget, event.widget.cget("font"))
            text_width = font.measure(key_text) + 6  # 加6像素留出内边距
            # 输入框宽度不超过单元格宽度，起始位置为文本的x坐标
            entry_width = min(text_width, width - (x - bbox[0]))
            entry_x = x
        except Exception:
            entry_width = width
            entry_x = x

        entry_copy = DEntry(event.widget)
        entry_copy.insert('end', key_text)
        entry_copy.icursor('end')
        entry_copy.config(state='readonly')  # 插入完成后再锁定为只读

        # 保存所属控件，用于销毁时恢复焦点
        entry_copy.tree_widget = event.widget

        def close_copy_entry(event=None):
            """关闭并销毁复制框（参照值列的销毁逻辑）"""
            self.treeview_lang.unbind_all("<MouseWheel>")
            self.scrollbar_treeview_y.unbind('<B1-Motion>')
            self.scrollbar_treeview_y.unbind("<MouseWheel>")
            try:
                entry_copy.unbind_all("<FocusOut>")
                entry_copy.destroy()
            except Exception:
                pass
            finally:
                # 【修复2】将焦点还给 Treeview，而不是 event.widget (即将销毁的输入框)
                try:
                    entry_copy.tree_widget.focus_set()
                except Exception:
                    pass

        # 将输入框放置到对应位置
        entry_copy.place(x=entry_x, y=y, width=entry_width, height=height)
        
        # 绑定销毁逻辑（与值列保持一致）
        entry_copy.bind("<Escape>", close_copy_entry)
        entry_copy.bind("<FocusOut>", close_copy_entry)
        # 只读框回车直接关闭，无需应用编辑
        entry_copy.bind("<Return>", close_copy_entry)
        
        # 滚动或拖拽滚动条时也要关闭，防止错位
        self.treeview_lang.bind("<MouseWheel>", close_copy_entry)
        self.scrollbar_treeview_y.bind('<B1-Motion>', close_copy_entry)
        self.scrollbar_treeview_y.bind("<MouseWheel>", close_copy_entry)
        
        # 聚焦并全选文本，方便用户直接 Ctrl+C 复制
        entry_copy.focus_set()
        entry_copy.select_range(0, tk.END)

        return "break"

    def get_tree_full_path(self, item_id):
        """
        获取Treeview节点的完整键名路径
        """
        path = []
        current = item_id

        while current:
            item = self.treeview_lang.item(current)
            path.insert(0, item['text'])
            current = self.treeview_lang.parent(current)

        return ".".join(path)

    def collect_node_text(self, item_id, prefix, lines):
        """
        递归收集节点及其所有子项的文本（同时用于选中子树与全树转换）
        """
        item = self.treeview_lang.item(item_id)
        text = item['text']
        values = item['values']
        value = values[0] if values else ""
        
        current_key = f"{prefix}.{text}" if prefix else text
        
        if value:  # 有值的节点
            lines.append(f"{current_key}={value}")
        
        for child in self.treeview_lang.get_children(item_id):
            self.collect_node_text(child, current_key, lines)

    def update_text_content(self, event=None):
        """
        更新右侧文本框，并同步路径框（不写入历史）。
        """
        selected_item = self.treeview_lang.focus()
        if not selected_item:
            return

        # 自动填入路径，不计入历史
        full_path = self.get_tree_full_path(selected_item)
        self.set_path_from_selection(full_path)
        self._record_path_nav(full_path)  # 写入路径导航栈（非 combobox 历史）

        lines = []
        parent_path = self.get_tree_full_path(self.treeview_lang.parent(selected_item))
        self.collect_node_text(selected_item, parent_path, lines)

        self.text_lang['state'] = 'normal'
        self.text_lang.delete(0.0, 'end')
        if lines:
            self.text_lang.insert(0.0, '\n'.join(lines))
        self.text_lang['state'] = 'disabled'

    def convert_tree_to_text(self,event=None,update_text=False):
        lines = []
        # 获取所有顶级节点
        for item in self.treeview_lang.get_children(""):
            self.collect_node_text(item, "", lines)
        output_text = '\n'.join(lines)
        if update_text:
            self.text_lang.config(state='normal')
            self.text_lang.delete(0.0, 'end')
            self.text_lang.insert('end', output_text)
            self.text_lang.config(state='disabled')
            self.button_output.config(text='\uE081')
            self.root.after(500,lambda:self.button_output.config(text='\uF714'))
        return output_text

    def open_search_window(self, event=None,replace=False):
        try:
            self.search_window.config()
        except:
            pass
        else:
            self.search_window.focus()
            win32api.MessageBeep()
            return

        def close_search_window(event=None):
            self.search_window.destroy()
            self.root.focus_set()
        def update_button_focus(event=None):
            if self.search_window.focus_get() == cancel_btn:
                button_search_up['default']='normal'
                button_search_down['default']='normal'
                button_replace['default']='normal'
                cancel_btn['default'] = 'active'
            elif self.search_window.focus_get() == button_search_up:
                button_search_up['default']='active'
                button_search_down['default']='normal'
                button_replace['default']='normal'
                cancel_btn['default'] = 'normal'
            elif self.search_window.focus_get() == button_search_down:
                button_search_up['default']='normal'
                button_search_down['default']='active'
                button_replace['default']='normal'
                cancel_btn['default'] = 'normal'
            elif self.search_window.focus_get() == button_replace:
                if var_replace.get():
                    button_search_up['default']='normal'
                    button_search_down['default']='normal'
                    button_replace['default']='active'
                    cancel_btn['default'] = 'normal'
                else:
                    button_search_up['default']='normal'
                    button_search_down['default']='active'
                    button_search_down.focus()
                    button_replace['default']='normal'
                    cancel_btn['default'] = 'normal' 
            elif cancel_btn.default== 'active':
                    if var_replace.get():
                        button_search_up['default']='normal'
                        button_search_down['default']='normal'
                        button_replace['default']='active'
                        cancel_btn['default']='normal'
                    else:
                        button_search_up['default']='normal'
                        button_search_down['default']='active'
                        button_replace['default']='normal'
                        cancel_btn['default']='normal'
                # 其它情况（比如焦点从向上查找移出），保持当前 active 状态不变
        # 查找状态（同一查询内记录是否已耗尽展开区域）
        search_phase = 'expanded'      # 'expanded' | 'full'
        last_search_query = None

        def search(search_direction='down'):
            nonlocal search_phase, last_search_query
            query = entry_search.get().strip()
            if not query:
                win32api.MessageBeep()
                entry_search.focus()
                return

            # 查询内容变化时，重置为优先展开阶段
            if query != last_search_query:
                last_search_query = query
                search_phase = 'expanded'

            def get_all_items(parent=''):
                items = []
                for child in self.treeview_lang.get_children(parent):
                    items.append(child)
                    items.extend(get_all_items(child))
                return items

            def get_expanded_items(parent=''):
                #仅当前已展开的可见节点
                items = []
                for child in self.treeview_lang.get_children(parent):
                    items.append(child)
                    if self.treeview_lang.item(child, 'open'):
                        items.extend(get_expanded_items(child))
                return items

            def match_item(item):
                item_text = self.treeview_lang.item(item, 'text')
                values = self.treeview_lang.item(item, 'values')
                value = values[0] if values else ''
                strict = var_strict_search.get()
                case_sensitive = var_case_sensitive_search.get()

                if case_sensitive:
                    # 区分大小写：直接用原始字符串比较
                    text_cmp = item_text
                    value_cmp = str(value)
                    query_cmp = query
                else:
                    # 不区分大小写：全部转小写再比较
                    text_cmp = item_text.lower()
                    value_cmp = str(value).lower()
                    query_cmp = query.lower()

                if search_button_search_scope == 'key':
                    if strict:
                        return text_cmp == query_cmp
                    return query_cmp in text_cmp
                elif search_button_search_scope == 'value':
                    if strict:
                        return value_cmp == query_cmp
                    return query_cmp in value_cmp
                else:  # all
                    if strict:
                        return text_cmp == query_cmp or value_cmp == query_cmp
                    return query_cmp in text_cmp or query_cmp in value_cmp

            def find_in_list(items_list, allow_wrap=True):
                #在列表中按方向查找。allow_wrap=False 时只走一遍，不回绕
                if not items_list:
                    return None
                current = self.treeview_lang.focus()
                try:
                    start_idx = items_list.index(current)
                except ValueError:
                    start_idx = -1

                n = len(items_list)
                if search_direction == 'down':
                    order = list(range(start_idx + 1, n))
                    if allow_wrap and var_loop_search.get():
                        order += list(range(0, start_idx + 1))
                else:
                    order = list(range(start_idx - 1, -1, -1))
                    if allow_wrap and var_loop_search.get():
                        order += list(range(n - 1, start_idx - 1, -1))

                for idx in order:
                    if match_item(items_list[idx]):
                        return items_list[idx]
                return None

            found = None

            if search_phase == 'expanded':
                # 第一阶段：只在已展开区域找，且不循环（只走一遍）
                found = find_in_list(get_expanded_items(), allow_wrap=False)
                if not found:
                    # 展开区域已耗尽，切换到全量阶段
                    search_phase = 'full'
                    found = find_in_list(get_all_items(), allow_wrap=True)
            else:
                # 已经进入全量阶段
                found = find_in_list(get_all_items(), allow_wrap=True)

            if found:
                # 展开所有父节点
                parent = self.treeview_lang.parent(found)
                while parent:
                    self.treeview_lang.item(parent, open=True)
                    parent = self.treeview_lang.parent(parent)
                SetExpandedTreeviewRowColor(self.treeview_lang,)
                self.treeview_lang.selection_set(found)
                self.treeview_lang.focus(found)
                self.treeview_lang.see(found)
                self.update_text_content()
                entry_search.focus()
            else:
                temp_direction_text='向上' if search_direction=='up' else '向下'
                MessageBoxModern(
                    parent=self.search_window,
                    title='查找',
                    text_blod=f'{temp_direction_text}找不到"{query}"',
                    text='请检查输入并确保已开启循环查找.',
                    icon='info',
                    
                )
                entry_search.focus()

        self.search_window = tk.Toplevel(self.root)
        self.search_window.title('查找')
        self.search_window.geometry(f'450x220+{(self.search_window.winfo_screenwidth() - 450) // 2}+{(self.search_window.winfo_screenheight() - 170) // 2}')
        self.search_window.resizable(False, False)
        self.search_window['bg'] = WINDOWBG
        self.search_window.protocol('WM_DELETE_WINDOW', close_search_window)
        self.search_window.bind('<Escape>', close_search_window)
        self.search_window.wm_transient(self.root)



        tk.Label(self.search_window, text='查找内容:', anchor='w', bg=WINDOWBG, fg=TEXTFG).place(x=20, y=20, width=90, height=30)
        entry_search = DEntry(self.search_window, takefocus=True)
        entry_search.place(x=110, y=20, width=320, height=30)
        entry_search.focus()


        def change_replace_state():
            nonlocal search_button_search_scope
            if var_replace.get():
                button_replace.config(state='normal',takefocus=True)
                entry_replace.config(state='normal')
                search_button_search_scope = 'value'
                button_search_scope.config(text='仅查找值',state='disabled')
                
            else:
                button_replace.config(state='disabled',takefocus=False)
                entry_replace.config(state='readonly')
                button_search_scope.config(state='normal')

        var_replace=tk.BooleanVar()
        var_replace.trace_add('write',lambda *_:change_replace_state())
        checkbutton_replace_label=tk.Checkbutton(self.search_window,text='替换为:',onvalue=True, offvalue=False, anchor='w',variable=var_replace,
                                                 bg=WINDOWBG,fg=TEXTFG,activebackground=WINDOWBG,activeforeground=TEXTFG,selectcolor=WIDGETBG)
        checkbutton_replace_label.place(x=20,y=70,width=90,height=30)

        entry_replace=DEntry(self.search_window,state='readonly')
        entry_replace.place(x=110,y=70,width=320,height=30)


        def change_search_button_search_scope():
                nonlocal search_button_search_scope
                if search_button_search_scope == 'all':
                    search_button_search_scope = 'key'
                    button_search_scope.config(text='仅查找键')
                elif search_button_search_scope == 'key':
                    search_button_search_scope = 'value'
                    button_search_scope.config(text='仅查找值')
                else:
                    search_button_search_scope = 'all'
                    button_search_scope.config(text='查找全部')
        search_button_search_scope = 'all'
        button_search_scope = DButton(self.search_window, text='查找全部', command=change_search_button_search_scope)
        button_search_scope.place(x=20, y=120, width=80, height=30)

        var_loop_search = tk.BooleanVar()
        var_loop_search.set(True)
        checkbutton_loop_search = tk.Checkbutton(self.search_window, text='循环查找', anchor='w',
                                                 variable=var_loop_search, onvalue=True, offvalue=False, 
                                                 bg=WINDOWBG,fg=TEXTFG,activebackground=WINDOWBG,activeforeground=TEXTFG,selectcolor=WIDGETBG)
        checkbutton_loop_search.place(x=120, y=120, width=90, height=30)

        var_case_sensitive_search = tk.BooleanVar()
        var_case_sensitive_search.set(False)
        checkbutton_case_sensitive_search = tk.Checkbutton(self.search_window, text='区分大小写', anchor='w',
                                                            variable=var_case_sensitive_search, onvalue=True, offvalue=False, 
                                                            bg=WINDOWBG,fg=TEXTFG,activebackground=WINDOWBG,activeforeground=TEXTFG,selectcolor=WIDGETBG,)
        
        checkbutton_case_sensitive_search.place(x=220, y=120, width=100, height=30)

        var_strict_search = tk.BooleanVar()
        var_strict_search.set(False)
        checkbutton_strict_search = tk.Checkbutton(self.search_window, text='严格查找', anchor='w', 
                                                variable=var_strict_search, onvalue=True, offvalue=False, 
                                                bg=WINDOWBG,fg=TEXTFG,activebackground=WINDOWBG,activeforeground=TEXTFG,selectcolor=WIDGETBG, )
        checkbutton_strict_search.place(x=340, y=120, width=90, height=30)


        def do_replace_on_item(item, query, replace_text, strict, case_sensitive):
            """对单个节点执行值替换。成功返回 True，否则 False。"""
            values = self.treeview_lang.item(item, 'values')
            value = values[0] if values else ''
            # 父节点（无值）不可替换
            if not value:
                return False

            if strict:
                # 严格：值必须与查找内容完全一致
                if case_sensitive:
                    if value != query:
                        return False
                else:
                    if value.lower() != query.lower():
                        return False
                new_value = replace_text
            else:
                # 非严格：子串匹配并替换所有出现处
                if case_sensitive:
                    if query not in value:
                        return False
                    new_value = value.replace(query, replace_text)
                else:
                    pattern = re.compile(re.escape(query), re.IGNORECASE)
                    if not pattern.search(value):
                        return False
                    new_value = pattern.sub(replace_text, value)

            # 与双击编辑一致：不允许结果为空或仅空白
            if new_value.replace(' ', '').replace('\t', '') == '':
                return False

            if new_value != value:
                self.treeview_lang.item(item, values=(new_value,))
                self.undo_manager.push('edit', item, value, new_value)
                self.is_modified = True
                self.update_title()
                return True
            return False

        def replace_action(event=None):
            """替换按钮逻辑：
            - 勾选「循环查找」：一次性替换所有符合条件的值
            - 未勾选：从当前选中行向下找第一项匹配并替换，再选中该项；下次继续向下
            仅作用于值列；严格查找要求值与查找内容完全一致。
            """
            query = entry_search.get()
            if not query.strip():
                win32api.MessageBeep()
                entry_search.focus()
                return

            replace_text = entry_replace.get()
            strict = var_strict_search.get()
            case_sensitive = var_case_sensitive_search.get()
            loop = var_loop_search.get()

            def get_all_items(parent=''):
                items = []
                for child in self.treeview_lang.get_children(parent):
                    items.append(child)
                    items.extend(get_all_items(child))
                return items

            def match_value(item):
                """判断节点值是否匹配查找条件（仅值）"""
                values = self.treeview_lang.item(item, 'values')
                value = values[0] if values else ''
                if not value:
                    return False
                if case_sensitive:
                    value_cmp = str(value)
                    query_cmp = query
                else:
                    value_cmp = str(value).lower()
                    query_cmp = query.lower()
                if strict:
                    return value_cmp == query_cmp
                return query_cmp in value_cmp

            all_items = get_all_items()

            if loop:
                # 全部替换
                count = 0
                last_item = None
                for item in all_items:
                    if match_value(item) and do_replace_on_item(item, query, replace_text, strict, case_sensitive):
                        count += 1
                        last_item = item
                if count > 0:
                    if last_item:
                        parent = self.treeview_lang.parent(last_item)
                        while parent:
                            self.treeview_lang.item(parent, open=True)
                            parent = self.treeview_lang.parent(parent)
                        SetExpandedTreeviewRowColor(self.treeview_lang)
                        self.treeview_lang.selection_set(last_item)
                        self.treeview_lang.focus(last_item)
                        self.treeview_lang.see(last_item)
                        self.update_text_content()
                    MessageBoxModern(
                        parent=self.search_window,
                        title='替换',
                        text_blod=f'已替换 {count} 处内容',
                        text=f'已将{count}个"{query}"替换为"{replace_text}".',
                        icon='correct',
                        )
                else:
                    win32api.MessageBeep()
                    MessageBoxModern(
                        parent=self.search_window,
                        title='替换',
                        text_blod=f'无可替换的"{query}"',
                        text='请检查输入内容,严格查找与区分大小写选项.',
                        icon='info',
                        )
                entry_search.focus()
            else:
                # 顺序替换：从当前选中行起向下找第一项匹配并替换（含当前行）
                # 若上一轮刚替换过当前行（值替换后仍可能匹配，如 a→aa），则从下一项开始，避免死循环
                current = self.treeview_lang.focus()
                try:
                    start_idx = all_items.index(current)
                except ValueError:
                    start_idx = 0

                last_replaced_id = getattr(replace_action, '_last_replaced_id', None)
                if current == last_replaced_id:
                    start_idx += 1

                found = None
                for idx in range(start_idx, len(all_items)):
                    if match_value(all_items[idx]):
                        found = all_items[idx]
                        break

                if found and do_replace_on_item(found, query, replace_text, strict, case_sensitive):
                    replace_action._last_replaced_id = found
                    parent = self.treeview_lang.parent(found)
                    while parent:
                        self.treeview_lang.item(parent, open=True)
                        parent = self.treeview_lang.parent(parent)
                    SetExpandedTreeviewRowColor(self.treeview_lang)
                    self.treeview_lang.selection_set(found)
                    self.treeview_lang.focus(found)
                    self.treeview_lang.see(found)
                    self.update_text_content()
                    entry_search.focus()
                else:
                    replace_action._last_replaced_id = None
                    win32api.MessageBeep()
                    MessageBoxModern(
                        parent=self.search_window,
                        title='替换',
                        text_blod=f'向下找不到可替换的"{query}"',
                        text='请检查输入，或勾选「循环查找」以替换全部匹配项。',
                        icon='info',
                        
                    )
                    entry_search.focus()

        button_replace=DButton(self.search_window, text='替换', command=replace_action, state='disabled')
        button_replace.place(x=50, y=170, width=80, height=30)


        button_search_up=DButton(self.search_window, text='向上查找', command=lambda:search(search_direction='up'), )
        button_search_up.place(x=150, y=170, width=80, height=30)

        button_search_down=DButton(self.search_window, text='向下查找', command=lambda:search(search_direction='down'),)
        button_search_down.place(x=250, y=170, width=80, height=30)

        cancel_btn = DButton(self.search_window, text='取消', command=close_search_window)
        cancel_btn.place(x=350, y=170, width=80, height=30)

        button_search_up.bind('<FocusIn>', update_button_focus)
        button_search_up.bind('<FocusOut>', update_button_focus)
        button_search_down.bind('<FocusIn>', update_button_focus)
        button_search_down.bind('<FocusOut>', update_button_focus)
        cancel_btn.bind('<FocusIn>', update_button_focus)
        cancel_btn.bind('<FocusOut>', update_button_focus)
        button_replace.bind('<FocusIn>', update_button_focus)
        button_replace.bind('<FocusOut>', update_button_focus)


        var_replace.set(replace)#注意顺序
        if var_replace.get():
            button_replace.config(default='active')
        else:
            button_search_down.config(default='active')
        self.search_window.wm_iconbitmap(f'{libresource}mclangtool.ico')
        SetDarkTitleBar(self.search_window)
        self.search_window.wait_window(self.search_window)

    def sort_tree_by_custom_order(self, parent=''):
        """
        将树中所有节点（无论是否折叠）按以下优先级重新排序：
        特殊符号 → 数字 → 大写字母 A-Z → 小写字母 a-z → 其它
        同一类别内支持自然排序（如 1, 2, ..., 10, 11 而不是 1, 10, 2）。
        """
        def natural_sort_key(text):
            """
            生成自然排序的键，将字符串拆分为文本和数字的混合列表
            例如: "item10b" -> ["item", 10, "b"]
            """
            if not text:
                return (5, [""])
            
            first = text[0]
            # 1. 确定大类优先级
            if not first.isalnum() and not ('\u4e00' <= first <= '\u9fff'):  # 特殊符号（排除中文）
                priority = 0
            elif first.isdigit():
                priority = 1
            elif first.isupper():
                priority = 2
            elif first.islower():
                priority = 3
            else:
                priority = 4  # 其它（含中文等）
            
            # 2. 将字符串拆分为 [文本, 数字, 文本, 数字...] 的列表
            parts = []
            for part in re.split(r'(\d+)', text):
                if part.isdigit():
                    parts.append(int(part))  # 数字部分转为整数，确保按数值大小排序
                elif part:
                    parts.append(part.lower())  # 文本部分统一转小写，确保忽略大小写排序
            
            # 返回元组：先按优先级排序，同优先级内按自然拆分列表排序
            return (priority, parts)

        children = list(self.treeview_lang.get_children(parent))
        if not children:
            return

        # 按自定义规则排序
        children.sort(key=lambda iid: natural_sort_key(self.treeview_lang.item(iid, 'text')))

        # 重新排列子节点顺序
        for index, iid in enumerate(children):
            self.treeview_lang.move(iid, parent, index)
            # 递归排序子树
            self.sort_tree_by_custom_order(iid)

        # 仅在根调用时刷新颜色
        if parent == '':
            SetExpandedTreeviewRowColor(self.treeview_lang)

    def reset_all(self,):
        for item in self.treeview_lang.get_children():
            self.treeview_lang.delete(item)
        self.entry_file.config(state='normal')
        self.entry_file.delete(0, 'end')
        self.entry_file.insert('end','',)
        self.entry_file.config(state='readonly')
        self.text_lang.config(state='normal')
        self.text_lang.delete(0.0,'end')
        self.text_lang.config(state='disabled')
        self.combobox_path.delete(0,'end')
        self.combobox_path.config(values=[])
        self.is_modified=False
        self.update_title()

        # 【修复】原代码调用 __init__() 会导致 UI 绑定异常丢失，现改为仅清空撤销栈
        self.path_nav_history = []
        self.path_nav_index = -1
        self.undo_manager.clear()

    def do_reset_all(self,):
        if MessageBoxModern(parent=self.root,text='未保存的更改将被丢弃,然后软件界面将会重置.',title='警告',text_blod='放弃所做的更改并重置?',icon='warning',button_mode=2,default_focus=2,text_true='重置',)==True:
            self.LANG_EDITION=None
            self.reset_all()

    def expand_selected(self,event=None):
        """展开所选节点及其所有子节点"""

        selected_item = self.treeview_lang.focus()
        if selected_item:
            # 展开当前选中的节点
            self.treeview_lang.item(selected_item, open=True)
            # 递归展开所有子节点
            for child in self.treeview_lang.get_children(selected_item):
                self.treeview_lang.item(child, open=True)
                # 递归处理子节点的子节点
                for grandchild in self.treeview_lang.get_children(child):
                    self.treeview_lang.item(grandchild, open=True)
            # 更新颜色
            winsound.PlaySound(f"{libresource}navigate.wav", winsound.SND_FILENAME | winsound.SND_ASYNC)
            SetExpandedTreeviewRowColor(self.treeview_lang)
            if not hasattr(self, '_expanded_by_expand_selected'):
                        self._expanded_by_expand_selected = set()

    def expand_all(self,event=None):
        """展开树中所有节点"""
        # 递归展开所有节点
        def expand_all_recursive(parent):
            for child in self.treeview_lang.get_children(parent):
                self.treeview_lang.item(child, open=True)
                expand_all_recursive(child)
        
        expand_all_recursive('')
        winsound.PlaySound(f"{libresource}navigate.wav", winsound.SND_FILENAME | winsound.SND_ASYNC)
        # 更新颜色
        SetExpandedTreeviewRowColor(self.treeview_lang)

    def collapse_selected(self,event=None):
        """收起所选节点（保留其直接子节点为展开状态）"""
        selected_item = self.treeview_lang.focus()
        if selected_item:
            # 只收起当前选中的节点，不改变其子节点的展开状态
            self.treeview_lang.item(selected_item, open=False)
            # 更新颜色
            winsound.PlaySound(f"{libresource}navigate.wav", winsound.SND_FILENAME | winsound.SND_ASYNC)
            SetExpandedTreeviewRowColor(self.treeview_lang)
            
            if hasattr(self, '_expanded_by_expand_selected'):
                self._expanded_by_expand_selected.discard(selected_item)       

    def collapse_all(self,event=None):
        """收起树中所有节点"""
        # 递归收起所有节点
        def collapse_all_recursive(parent):
            for child in self.treeview_lang.get_children(parent):
                self.treeview_lang.item(child, open=False)
                collapse_all_recursive(child)
        
        collapse_all_recursive('')
        winsound.PlaySound(f"{libresource}navigate.wav", winsound.SND_FILENAME | winsound.SND_ASYNC)
        # 更新颜色
        SetExpandedTreeviewRowColor(self.treeview_lang)

    def toggle_expand_selected(self, event=None):
        """快捷键：已展开则收起所选，否则展开所选。"""
        selected = self.treeview_lang.focus()
        if not selected:
            return "break"
        if self.treeview_lang.item(selected, 'open'):
            self.collapse_selected()
        else:
            self.expand_selected()
        return "break"

    def _on_middle_press(self, event):
        """中键按下：记录原点，开始自动滚动循环"""
        self._middle_origin_y = event.y_root          # 使用屏幕坐标，鼠标离开控件也有效
        self._middle_dragging = True
        self.root.config(cursor="sb_v_double_arrow")
        self._middle_scroll_loop()

    def _middle_scroll_loop(self):
        """持续滚动循环：速度只与当前鼠标到原点的距离成正比"""
        if not getattr(self, '_middle_dragging', False):
            return

        # 当前鼠标的屏幕 Y 坐标
        current_y = self.root.winfo_pointery()
        delta = current_y - self._middle_origin_y

        # 死区：离原点太近不滚动（约 8 像素）
        if abs(delta) > 8:
            # 速度与距离成正比，可调整系数（越大越快）
            # 使用 units，与表格展开数量无关
            speed = int(delta / 50)          # 25 是灵敏度，可改成 20~40 之间
            if speed == 0:
                speed = 1 if delta > 0 else -1
            self.treeview_lang.yview_scroll(speed, "units")

        # 约 30ms 执行一次，手感比较流畅
        self.root.after(30, self._middle_scroll_loop)

    def _on_middle_release(self, event):
        """中键松开：立刻停止滚动并恢复光标"""
        self._middle_dragging = False
        self.root.config(cursor="arrow")

    def _record_path_nav(self, path):
        """将路径压入导航栈（与 combobox_path 下拉历史无关）。
        前进/后退操作自身不会写入。"""
        if self._suppress_path_nav_record or not path:
            return
        # 与栈顶当前位置相同则忽略
        if (0 <= self.path_nav_index < len(self.path_nav_history)
                and self.path_nav_history[self.path_nav_index] == path):
            return
        # 若不在栈顶，丢弃「前进」方向的记录
        if self.path_nav_index < len(self.path_nav_history) - 1:
            self.path_nav_history = self.path_nav_history[:self.path_nav_index + 1]
        self.path_nav_history.append(path)
        self.path_nav_index = len(self.path_nav_history) - 1

    def go_previous_path(self, event=None):
        """上一路径；已到栈底则不做任何事。"""
        if self.path_nav_index <= 0:
            return
        self.path_nav_index -= 1
        path = self.path_nav_history[self.path_nav_index]
        if not self.treeview_lang.exists(path):
            return
        self._suppress_path_nav_record = True
        try:
            self.set_path_from_selection(path)
            self.navigate_to_exact_path(path)  # 内部已 PlaySound
        finally:
            self._suppress_path_nav_record = False

    def go_next_path(self, event=None):
        """下一路径；已到栈顶则不做任何事。"""
        if self.path_nav_index >= len(self.path_nav_history) - 1:
            return
        self.path_nav_index += 1
        path = self.path_nav_history[self.path_nav_index]
        if not self.treeview_lang.exists(path):
            return
        self._suppress_path_nav_record = True
        try:
            self.set_path_from_selection(path)
            self.navigate_to_exact_path(path)  # 内部已 PlaySound
        finally:
            self._suppress_path_nav_record = False

    def on_path_text_changed(self):
        """路径文字变化时：只更新背景色，不跳转、不写历史。"""
        if self.updating_path:
            return
        self._update_path_bg()

    def on_path_return(self, event=None):
        """用户按回车：若路径存在则跳转并写入历史。"""
        path = self._get_normalized_path()
        if not path:
            return
        if self.treeview_lang.exists(path):
            self.navigate_to_exact_path(path)
            self.add_path_to_history(path)
        else:
            win32api.MessageBeep()

    def on_path_committed(self):
        """下拉选择 / 滚轮 / 上下键确认后：跳转并写入历史。"""
        path = self._get_normalized_path()
        if not path:
            return
        if self.treeview_lang.exists(path):
            self.navigate_to_exact_path(path)
            self.add_path_to_history(path)

    def _get_normalized_path(self):
        """取出并规范化当前路径文本。"""
        return self.var_entry_path.get().rstrip('.').strip()

    def _update_path_bg(self):
        """根据路径是否存在，更新路径框背景色。"""
        path = self._get_normalized_path()
        if path and self.treeview_lang.exists(path):
            self.combobox_path.config(bg=AlphaBlend(GREENLIGHT, WIDGETBG, 0.2))
        else:
            self.combobox_path.config(bg=WIDGETBG)

    def set_path_from_selection(self, path):
        """
        由表格选中项驱动时调用：
        只填充路径框并刷新颜色，不写入历史、不触发跳转。
        """
        self.updating_path = True
        try:
            self.var_entry_path.set(path)
            self._update_path_bg()
        finally:
            self.updating_path = False

    def add_path_to_history(self, path):
        """
        将路径插入下拉历史记录头部。
        即使该路径曾经出现过，也不删除旧记录，允许重复保留多次浏览痕迹。
        """
        if not path:
            return
        values = list(self.combobox_path.values or [])
        values.insert(0, path)
        self.combobox_path.config(values=values)

    def navigate_to_exact_path(self, path):
        """展开父节点 → 选中 → 聚焦 → 可见->播放声音 → 刷新右侧文本。"""
        try:
            if not self.treeview_lang.exists(path):
                return
            parent = self.treeview_lang.parent(path)
            while parent:
                self.treeview_lang.item(parent, open=True)
                parent = self.treeview_lang.parent(parent)

            SetExpandedTreeviewRowColor(self.treeview_lang)
            self.treeview_lang.selection_set(path)
            self.treeview_lang.focus(path)
            self.treeview_lang.see(path)
            winsound.PlaySound(f"{libresource}navigate.wav", winsound.SND_FILENAME | winsound.SND_ASYNC)
            self.update_text_content()
        except Exception as e:
            MessageBoxModern(
                parent=self.root,
                title='错误',
                text_blod='导航到路径失败',
                text=e,
                icon='error',
                
            )
            self.combobox_path.config(bg=WIDGETBG)

    def help(self,event=None):
        MessageBoxModern(parent=self.root,title='帮助',text='请加入QQ群865302820寻求帮助,因为我暂时还没写帮助文档.',text_blod="暂无帮助文档",icon='info')

    def about(self,event=None):
        def set_label_font(label, add_size=3,bold=False):
            old_font = tkfont.Font(font=label.cget("font"))
            new_font = old_font.copy()
            new_font.configure(weight="bold" if bold else "normal", size=old_font.cget("size") + add_size)
            label.configure(font=new_font)

        def close_about_window(event=None):
            self.root.attributes('-disabled', False)
            self.about_window.destroy()
            self.root.focus_set()
        self.root.attributes('-disabled', True)
        self.about_window = tk.Toplevel(self.root)
        self.about_window.title('关于')
        self.about_window.geometry(f'800x570+{(self.about_window.winfo_screenwidth() - 800) // 2}+{(self.about_window.winfo_screenheight() - 570) // 2}')
        self.about_window.resizable(False, False)
        self.about_window['bg'] = WINDOWBG
        self.about_window.protocol('WM_DELETE_WINDOW', close_about_window)
        self.about_window.bind('<Escape>', close_about_window)
        self.about_window.wm_transient(self.root)
        self.about_window.focus()

        label_icon=tk.Label(self.about_window,bg=WINDOWBG)
        SetImageTk(label_icon,f"{libresource}mclangtool.ico",[64,64])
        label_icon.place(x=20,y=20,width=70,height=70)

        label_title=tk.Label(self.about_window,bg=WINDOWBG,text='万岁™Minecraft多语言编辑器',anchor='w',fg=TEXTFG)
        set_label_font(label_title,add_size=18,bold=True)
        label_title.place(x=110,y=20,width=670,height=70)

        tk.Label(self.about_window,bg=TEXTBG,fg=TEXTFG,).place(x=20,y=120,width=760,height=2)

        tk.Label(self.about_window,bg=WINDOWBG,fg=TEXTFG,text='软件概述:',anchor='w').place(x=20,y=140,width=90,height=30)
        label_introduction=tk.Label(self.about_window,bg=WINDOWBG,fg=SECONDARYTEXTFG,text='一款以树状图形式呈现并编辑Minecraft语言文件的编辑软件.',anchor='w')
        label_introduction.place(x=110,y=140,height=30)
        BindTipWindow(label_introduction,text="万岁老桃首创\"树状图+文本框\"双工作区模式,让预览与编辑融为一体!",width=450)


        tk.Label(self.about_window,bg=WINDOWBG,fg=TEXTFG,text='当前版本:',anchor='w').place(x=20,y=180,width=90,height=30)
        tk.Label(self.about_window,bg=WINDOWBG,fg=SECONDARYTEXTFG,text=f'V{VERSION}',anchor='w').place(x=110,y=180,height=30)

        tk.Label(self.about_window,bg=TEXTBG,fg=TEXTFG,).place(x=20,y=230,width=760,height=2)

        tk.Label(self.about_window,bg=WINDOWBG,fg=TEXTFG,text='著作权:',anchor='w').place(x=20,y=250,width=90,height=30)
        label_copyright=tk.Label(self.about_window,bg=WINDOWBG,fg=TEXTFG,text='Copyright © 2026-2031 炸图监管者 · Licensed under the MIT License.',anchor='w')
        label_copyright.place(x=110,y=250,height=30)
        BindTipWindow(label_copyright,text=MITLICENSE,width=600)

        tk.Label(self.about_window,bg=TEXTBG,fg=TEXTFG,).place(x=20,y=300,width=760,height=2)

        tk.Label(self.about_window,bg=WINDOWBG,fg=TEXTFG,text='相关链接:',anchor='w').place(x=20,y=320,width=90,height=30)


        label_github=tk.Label(self.about_window,bg=WINDOWBG,fg=SECONDARYTEXTFG,text='Github:',anchor='w',)
        label_github.place(x=60,y=360,width=90,height=30)

        button_github=DAlphaButton(self.about_window,text='https://github.com/zhatujianguanzhe',command=lambda:webbrowser.open_new_tab("https://github.com/zhatujianguanzhe"),fg=LINK,anchor='w')
        button_github.place(x=150,y=360,height=30)

        label_discord=tk.Label(self.about_window,bg=WINDOWBG,fg=SECONDARYTEXTFG,text='Discord:',anchor='w',)
        label_discord.place(x=60,y=400,width=90,height=30)

        button_discord=DAlphaButton(self.about_window,text='https://discord.gg/Ukr55F2Ypc',command=lambda:webbrowser.open_new_tab("https://discord.gg/Ukr55F2Ypc"),fg=LINK,anchor='w')
        button_discord.place(x=150,y=400,height=30)

        label_bilibili=tk.Label(self.about_window,bg=WINDOWBG,fg=SECONDARYTEXTFG,text='Bilibili:',anchor='w',)
        label_bilibili.place(x=60,y=440,width=90,height=30)

        button_bilibili=DAlphaButton(self.about_window,text='https://space.bilibili.com/1342104465',command=lambda:webbrowser.open_new_tab("https://space.bilibili.com/1342104465"),fg=LINK,anchor='w')
        button_bilibili.place(x=150,y=440,height=30)

        label_qq=tk.Label(self.about_window,bg=WINDOWBG,fg=SECONDARYTEXTFG,text='QQ群:',anchor='w',)
        label_qq.place(x=60,y=480,width=90,height=30)

        button_qq=tk.Label(self.about_window,text='865302820',bg=WINDOWBG,fg=SECONDARYTEXTFG,anchor='w')
        button_qq.place(x=150,y=480,height=30)

        button_close_about=DButton(self.about_window,text='关闭',default='active',command=close_about_window)
        button_close_about.place(x=700,y=520,width=80,height=30)

        SetDarkTitleBar(self.about_window)
        self.about_window.wm_iconbitmap(f"{libresource}mclangtool.ico")
        self.about_window.wait_window()



if __name__ == '__main__':
    a=MCLangTools()
    a.run_app()
