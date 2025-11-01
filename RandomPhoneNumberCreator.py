import pickle
import random
import threading
import tkinter as tk
from datetime import datetime
from tkinter import ttk, messagebox, scrolledtext, filedialog
import os
import sys
import traceback


class PhoneNumberGenerator:
    def __init__(self, root):
        self.root = root
        self.root.title("手机号码随机生成器")
        self.root.geometry("800x700")  # 增加默认窗口大小
        self.root.configure(bg='#F0F0F0')
        self.root.minsize(600, 500)  # 设置最小窗口大小

        # 绑定窗口大小变化事件
        self.root.bind('<Configure>', self.on_window_resize)

        # 设置程序异常处理
        self.setup_exception_handling()

        # 配置常量
        self.BATCH_SIZE = 1000  # 批处理大小
        self.current_font_size = 9  # 当前字体大小

        # 手机号前缀
        self.beginner = ['134', '135', '136', '137', '138', '139', '147', '150',
                         '151', '152', '157', '158', '159', '182', '187', '188',
                         '130', '131', '132', '155', '156', '185', '186', '133',
                         '153', '180', '189', '173', '177', '199', '166', '198',
                         '191', '193', '149']

        self.generated_numbers = []
        self.is_generating = False
        self.generation_thread = None

        # 运营商选择变量
        self.operator_vars = {
            "中国移动": tk.BooleanVar(value=True),
            "中国联通": tk.BooleanVar(value=True),
            "中国电信": tk.BooleanVar(value=True)
        }

        self.setup_ui()

    def on_window_resize(self, event):
        """窗口大小变化时的响应处理"""
        if event.widget == self.root:
            # 根据窗口宽度调整字体大小
            width = event.width
            if width > 1000:
                new_font_size = 11
            elif width > 800:
                new_font_size = 10
            elif width > 600:
                new_font_size = 9
            else:
                new_font_size = 8

            if new_font_size != self.current_font_size:
                self.current_font_size = new_font_size
                self.update_font_sizes()

    def update_font_sizes(self):
        """更新所有字体大小"""
        # 更新结果显示区域的字体
        self.results_text.config(font=("Consolas", self.current_font_size))

        # 更新状态栏字体
        for widget in self.root.winfo_children():
            if isinstance(widget, ttk.Frame):
                self.update_child_fonts(widget)

    def update_child_fonts(self, parent):
        """递归更新子组件的字体"""
        for child in parent.winfo_children():
            if isinstance(child, ttk.Label):
                try:
                    current_font = child.cget('font')
                    if current_font:
                        # 只修改字体大小，保持字体族不变
                        font_parts = current_font.split()
                        if len(font_parts) >= 2:
                            new_font = (font_parts[0], self.current_font_size)
                            if len(font_parts) > 2:
                                new_font += tuple(font_parts[2:])
                            child.config(font=new_font)
                except:
                    pass
            elif isinstance(child, (ttk.Frame, ttk.PanedWindow)):
                self.update_child_fonts(child)

    def setup_exception_handling(self):
        """设置全局异常处理"""

        def handle_exception(exc_type, exc_value, exc_traceback):
            if issubclass(exc_type, KeyboardInterrupt):
                sys.__excepthook__(exc_type, exc_value, exc_traceback)
                return

            error_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
            print(f"未处理的异常: {error_msg}")

            # 在UI线程中显示错误
            if hasattr(self, 'root') and self.root.winfo_exists():
                self.root.after(0, lambda: messagebox.showerror(
                    "程序错误",
                    f"发生未处理的异常:\n{str(exc_value)}\n\n详细信息已记录。"
                ))

        sys.excepthook = handle_exception

    def setup_ui(self):
        # 创建主框架 - 使用grid布局以获得更好的响应式控制
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 标题 - 居中显示
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 15))

        title_label = ttk.Label(title_frame, text="手机号码随机生成器",
                                font=("Arial", 16, "bold"))
        title_label.pack(expand=True)

        # 创建可调整的paned window用于主要区域
        self.main_paned = ttk.PanedWindow(main_frame, orient=tk.VERTICAL)
        self.main_paned.pack(fill=tk.BOTH, expand=True)

        # 上部区域 - 控制面板
        control_frame = ttk.Frame(self.main_paned, padding="5")
        self.main_paned.add(control_frame, weight=1)

        # 输入框架 - 使用grid布局
        input_frame = ttk.Frame(control_frame)
        input_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(input_frame, text="生成数量:").grid(row=0, column=0, sticky="w", padx=(0, 5))

        # 使用带验证的Spinbox
        vcmd = (self.root.register(self.validate_spinbox_input), '%P')
        self.count_spinbox = tk.Spinbox(
            input_frame,
            from_=1,
            to=1000000,
            width=12,  # 增加宽度
            font=("Arial", 10),
            validate="key",
            validatecommand=vcmd
        )
        self.count_spinbox.delete(0, tk.END)
        self.count_spinbox.insert(0, "10")
        self.count_spinbox.grid(row=0, column=1, sticky="w", padx=(0, 5))
        self.count_spinbox.bind('<Return>', lambda event: self.generate_numbers())

        # 添加恢复默认值按钮
        self.reset_count_btn = ttk.Button(input_frame, text="恢复默认",
                                          command=self.reset_to_default)
        self.reset_count_btn.grid(row=0, column=2, sticky="w", padx=(5, 0))

        # 让输入框架的列可以扩展
        input_frame.columnconfigure(3, weight=1)

        # 运营商选择框架 - 自适应布局
        operator_frame = ttk.Frame(control_frame)
        operator_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(operator_frame, text="运营商选择:").pack(side=tk.LEFT)

        # 创建运营商复选框容器 - 使用Frame包装以便更好地控制布局
        operator_buttons_frame = ttk.Frame(operator_frame)
        operator_buttons_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 0))

        self.mobile_cb = ttk.Checkbutton(operator_buttons_frame, text="中国移动",
                                         variable=self.operator_vars["中国移动"])
        self.mobile_cb.pack(side=tk.LEFT, padx=(0, 10))

        self.unicom_cb = ttk.Checkbutton(operator_buttons_frame, text="中国联通",
                                         variable=self.operator_vars["中国联通"])
        self.unicom_cb.pack(side=tk.LEFT, padx=(0, 10))

        self.telecom_cb = ttk.Checkbutton(operator_buttons_frame, text="中国电信",
                                          variable=self.operator_vars["中国电信"])
        self.telecom_cb.pack(side=tk.LEFT, padx=(0, 10))

        # 操作按钮框架 - 使用grid实现响应式布局
        button_container = ttk.Frame(control_frame)
        button_container.pack(fill=tk.X, pady=(0, 10))

        # 第一行按钮
        button_row1 = ttk.Frame(button_container)
        button_row1.pack(fill=tk.X, pady=(0, 5))

        self.generate_btn = ttk.Button(button_row1, text="生成号码",
                                       command=self.generate_numbers)
        self.generate_btn.pack(side=tk.LEFT, padx=(0, 5))

        self.clear_btn = ttk.Button(button_row1, text="清空结果",
                                    command=self.clear_results)
        self.clear_btn.pack(side=tk.LEFT, padx=(0, 5))

        self.stop_btn = ttk.Button(button_row1, text="停止生成",
                                   command=self.stop_generation,
                                   state="disabled")
        self.stop_btn.pack(side=tk.LEFT, padx=(0, 5))

        # 第二行按钮 - 文件操作
        button_row2 = ttk.Frame(button_container)
        button_row2.pack(fill=tk.X)

        self.save_btn = ttk.Button(button_row2, text="保存到文件",
                                   command=self.save_numbers)
        self.save_btn.pack(side=tk.LEFT, padx=(0, 5))

        self.load_btn = ttk.Button(button_row2, text="从文件读取",
                                   command=self.load_numbers)
        self.load_btn.pack(side=tk.LEFT, padx=(0, 5))

        self.export_btn = ttk.Button(button_row2, text="导出为文本",
                                     command=self.export_numbers)
        self.export_btn.pack(side=tk.LEFT, padx=(0, 5))

        self.about_btn = ttk.Button(button_row2, text="关于",
                                    command=self.show_about)
        self.about_btn.pack(side=tk.LEFT, padx=(0, 5))

        self.exit_btn = ttk.Button(button_row2, text="退出程序",
                                   command=self.exit_program)
        self.exit_btn.pack(side=tk.LEFT)

        # 让按钮行可以扩展
        button_row1.pack_configure(fill=tk.X)
        button_row2.pack_configure(fill=tk.X)

        # 统计信息和状态区域
        info_frame = ttk.Frame(control_frame)
        info_frame.pack(fill=tk.X, pady=(0, 10))

        self.stats_label = ttk.Label(info_frame, text="已生成: 0 个号码")
        self.stats_label.pack(side=tk.LEFT)

        # 状态栏 - 右对齐
        self.status_var = tk.StringVar(value="就绪")
        status_label = ttk.Label(info_frame, textvariable=self.status_var,
                                 foreground="blue")
        status_label.pack(side=tk.RIGHT)

        # 进度条
        self.progress = ttk.Progressbar(control_frame, mode='determinate')
        self.progress.pack(fill=tk.X, pady=(0, 10))

        # 下部区域 - 结果显示
        result_frame = ttk.Frame(self.main_paned, padding="5")
        self.main_paned.add(result_frame, weight=3)  # 给结果区域更多空间

        # 结果显示区域标题
        result_header = ttk.Frame(result_frame)
        result_header.pack(fill=tk.X, pady=(0, 5))

        ttk.Label(result_header, text="生成的手机号码:").pack(side=tk.LEFT)

        # 添加一个查看选项的小标签
        view_info = ttk.Label(result_header, text="(超过1000个号码时只显示前1000个)",
                              foreground="gray", font=("Arial", 8))
        view_info.pack(side=tk.RIGHT)

        # 可滚动的结果显示区域
        self.results_text = scrolledtext.ScrolledText(
            result_frame,
            height=15,
            width=80,
            font=("Consolas", self.current_font_size),
            wrap=tk.NONE  # 不自动换行
        )
        self.results_text.pack(fill=tk.BOTH, expand=True)

        # 添加水平滚动条
        h_scrollbar = ttk.Scrollbar(result_frame, orient=tk.HORIZONTAL,
                                    command=self.results_text.xview)
        h_scrollbar.pack(fill=tk.X)
        self.results_text.config(xscrollcommand=h_scrollbar.set)

        # 设置paned window的初始分割比例
        self.main_paned.sashpos(0, 300)

    def show_about(self):
        """显示关于信息"""
        about_text = """手机号码随机生成器

版本: 2.0
作者: 快速的飓风
版权所有 © 2025

功能说明:
- 随机生成指定数量的手机号码
- 支持选择特定运营商
- 保存和加载号码数据
- 导出为文本文件
- 响应式界面设计

本程序仅供学习和测试使用。"""

        messagebox.showinfo("关于", about_text)

    def reset_to_default(self):
        """恢复生成数量为默认值"""
        self.count_spinbox.delete(0, tk.END)
        self.count_spinbox.insert(0, "10")
        self.count_spinbox.focus_set()

    def validate_spinbox_input(self, new_value):
        """验证Spinbox输入，只允许数字和空值"""
        if new_value == "" or new_value.isdigit():
            return True
        return False

    def safe_get_spinbox_value(self):
        """安全获取Spinbox值，去除前缀0"""
        try:
            value = self.count_spinbox.get().strip()
            if not value:
                return 0

            # 去除前缀0，比如 "00100" -> "100"
            value = value.lstrip('0')

            # 如果去除0后变成空字符串，说明输入的是"0"或"00"等，返回0
            if not value:
                return 0

            return int(value)
        except ValueError:
            return 0

    def remove_leading_zeros_from_spinbox(self):
        """去除Spinbox中的前缀0并更新显示"""
        try:
            value = self.count_spinbox.get().strip()
            if value and value.startswith('0'):
                # 去除前缀0
                cleaned_value = value.lstrip('0')
                # 如果去除0后变成空字符串，说明输入的是"0"或"00"等，设置为"0"
                if not cleaned_value:
                    cleaned_value = "0"

                # 更新Spinbox显示
                self.count_spinbox.delete(0, tk.END)
                self.count_spinbox.insert(0, cleaned_value)
        except:
            pass

    def get_selected_operator_prefixes(self):
        """根据选中的运营商获取对应的号段前缀"""
        selected_prefixes = []
        operator_prefixes = {
            "中国移动": ['134', '135', '136', '137', '138', '139', '147', '150',
                         '151', '152', '157', '158', '159', '182', '187', '188'],
            "中国联通": ['130', '131', '132', '155', '156', '185', '186', '145', '176'],
            "中国电信": ['133', '153', '180', '189', '177', '173', '199']
        }

        for operator, var in self.operator_vars.items():
            if var.get():  # 如果该运营商被选中
                selected_prefixes.extend(operator_prefixes.get(operator, []))

        # 如果没有选择任何运营商，则使用全部前缀
        if not selected_prefixes:
            selected_prefixes = self.beginner

        return selected_prefixes

    def select_all_operators(self):
        """全选所有运营商"""
        for var in self.operator_vars.values():
            var.set(True)

    def select_none_operators(self):
        """全不选所有运营商"""
        for var in self.operator_vars.values():
            var.set(False)

    def invert_selection_operators(self):
        """反选运营商"""
        for var in self.operator_vars.values():
            var.set(not var.get())

    def validate_phone_number(self, number):
        """严格的手机号验证"""
        if len(number) != 11:
            return False
        if not number.isdigit():
            return False

        # 验证号段有效性
        valid_prefixes = ['130', '131', '132', '133', '134', '135', '136', '137',
                          '138', '139', '145', '147', '149', '150', '151', '152',
                          '153', '155', '156', '157', '158', '159', '165', '166',
                          '167', '170', '171', '172', '173', '174', '175', '176',
                          '177', '178', '180', '181', '182', '183', '184', '185',
                          '186', '187', '188', '189', '191', '192', '193', '195',
                          '196', '197', '198', '199']
        return number[:3] in valid_prefixes

    def get_default_filename(self, extension=".bin"):
        """生成包含当前系统时间的默认文件名"""
        current_time = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"phone_numbers_{current_time}{extension}"

    def check_memory_safe(self, estimated_count):
        """检查内存是否安全"""
        # 简单估算，如果数量过大给出警告
        if estimated_count > 1000000:  # 100万
            return False, "生成数量过大，可能会消耗大量内存和时间"
        elif estimated_count > 100000:  # 10万
            return True, "生成数量较大，建议分批操作"
        return True, "内存充足"

    def generate_numbers(self):
        # 首先去除Spinbox中的前缀0
        self.remove_leading_zeros_from_spinbox()

        if self.is_generating:
            messagebox.showwarning("操作进行中", "请等待当前生成操作完成")
            return

        count = self.safe_get_spinbox_value()

        if count <= 0:
            messagebox.showerror("输入错误", "请输入有效的数字！")
            self.count_spinbox.focus_set()
            return

        # 检查是否至少选择了一个运营商
        if not any(var.get() for var in self.operator_vars.values()):
            messagebox.showerror("选择错误", "请至少选择一个运营商！")
            return

        # 内存安全检查
        is_safe, message = self.check_memory_safe(count)
        if not is_safe:
            if not messagebox.askyesno("内存警告", f"{message}，是否继续？"):
                return
        elif count > 100000:  # 10万以上给出提示
            if not messagebox.askyesno("确认生成", f"将要生成 {count:,} 个号码，这可能需要较长时间，是否继续？"):
                return

        # 获取选择的运营商对应的前缀
        prefixes = self.get_selected_operator_prefixes()

        # 清空之前的结果
        self.results_text.delete(1.0, tk.END)
        self.generated_numbers = []

        # 更新UI状态
        self.generate_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.status_var.set("开始生成...")
        self.progress['value'] = 0
        self.progress['maximum'] = count

        # 在后台线程中生成号码
        self.generation_thread = threading.Thread(target=self.generate_numbers_thread,
                                                  args=(count, prefixes))
        self.generation_thread.daemon = True
        self.generation_thread.start()

    def generate_numbers_thread(self, count, prefixes):
        """在后台线程中生成号码"""
        try:
            self.is_generating = True
            generated_count = 0
            attempts = 0
            max_attempts = count * 50  # 增加尝试次数限制

            numbers_set = set()

            while generated_count < count and attempts < max_attempts and self.is_generating:
                # 批量生成
                batch_size = min(self.BATCH_SIZE, count - generated_count)
                batch_numbers = set()

                for _ in range(batch_size):
                    if not self.is_generating:
                        break

                    prefix = random.choice(prefixes)
                    suffix = ''.join(str(random.randint(0, 9)) for _ in range(8))
                    phone_number = f"{prefix}{suffix}"

                    if self.validate_phone_number(phone_number):
                        batch_numbers.add(phone_number)

                    attempts += 1
                    if attempts >= max_attempts:
                        break

                # 添加到主集合
                numbers_set.update(batch_numbers)
                generated_count = len(numbers_set)

                # 更新进度
                self.update_generation_progress(generated_count, count, attempts)

            self.generated_numbers = list(numbers_set)
            self.finalize_generation(generated_count, count, attempts < max_attempts)

        except MemoryError:
            self.root.after(0, lambda: messagebox.showerror("内存不足", "生成过程中内存不足，已停止"))
            self.finalize_generation(generated_count, count, False)
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("生成错误", f"生成过程中发生错误：{str(e)}"))
            self.finalize_generation(generated_count, count, False)
        finally:
            self.is_generating = False

    def update_generation_progress(self, current, total, attempts):
        """更新生成进度"""
        self.root.after(0, lambda: self._update_progress_ui(current, total, attempts))

    def _update_progress_ui(self, current, total, attempts):
        """在UI线程中更新进度"""
        self.progress['value'] = current
        self.status_var.set(f"正在生成... {current}/{total} (尝试次数: {attempts})")

    def finalize_generation(self, generated_count, target_count, success):
        """完成生成操作"""
        self.root.after(0, lambda: self._finalize_generation_ui(generated_count, target_count, success))

    def _finalize_generation_ui(self, generated_count, target_count, success):
        """在UI线程中完成生成"""
        self.results_text.delete(1.0, tk.END)

        # 分批显示结果，避免UI卡顿
        display_count = min(len(self.generated_numbers), 1000)  # 只显示前1000个
        for i, number in enumerate(self.generated_numbers[:display_count], 1):
            self.results_text.insert(tk.END, f"[{i}] {number}\n")

        if len(self.generated_numbers) > display_count:
            self.results_text.insert(tk.END,
                                     f"\n... 还有 {len(self.generated_numbers) - display_count} 个号码未显示，导出为文本查看完整内容。\n")

        self.stats_label.config(text=f"已生成: {generated_count} 个号码")

        if not success and generated_count < target_count:
            messagebox.showwarning("生成不完整",
                                   f"只生成了 {generated_count} 个有效号码（可能达到尝试次数限制）")

        # 显示选中的运营商
        selected_operators = [op for op, var in self.operator_vars.items() if var.get()]
        operators_text = ", ".join(selected_operators) if selected_operators else "全部"

        self.results_text.insert(tk.END, f"\n生成完毕！共生成 {generated_count} 个手机号码。")
        self.results_text.insert(tk.END, f"\n运营商: {operators_text}")
        self.results_text.insert(tk.END, f"\n生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        self.status_var.set("就绪")
        self.progress['value'] = 0
        self.generate_btn.config(state="normal")
        self.stop_btn.config(state="disabled")

    def stop_generation(self):
        """停止生成操作"""
        if self.is_generating:
            self.is_generating = False
            self.status_var.set("正在停止...")
            # 等待线程结束
            if self.generation_thread and self.generation_thread.is_alive():
                self.generation_thread.join(timeout=2.0)

    def validate_file_data(self, data):
        """验证加载的文件数据完整性"""
        if not isinstance(data, dict):
            return False, "文件格式错误：不是有效的字典数据"

        required_keys = ['numbers', 'count']
        for key in required_keys:
            if key not in data:
                return False, f"文件格式错误：缺少必要的键 '{key}'"

        if not isinstance(data['numbers'], list):
            return False, "文件格式错误：号码数据不是列表"

        if len(data['numbers']) != data['count']:
            return False, f"文件数据不一致：声明数量 {data['count']}，实际数量 {len(data['numbers'])}"

        # 验证每个号码
        for i, number in enumerate(data['numbers']):
            if not self.validate_phone_number(str(number)):
                return False, f"文件包含无效号码（第{i + 1}个）: {number}"

        return True, "数据验证通过"

    def save_numbers(self):
        """保存号码到二进制文件"""
        if not self.generated_numbers:
            messagebox.showwarning("无数据", "没有可保存的号码数据！")
            return

        default_filename = self.get_default_filename()

        filename = filedialog.asksaveasfilename(
            title="保存号码文件",
            defaultextension=".bin",
            filetypes=[("电话本文件", "*.bin"), ("所有文件", "*.*")],
            initialfile=default_filename
        )

        if filename:
            try:
                # 检查磁盘空间
                if not self.check_disk_space(filename, len(self.generated_numbers)):
                    if not messagebox.askyesno("磁盘空间警告", "磁盘空间可能不足，是否继续保存？"):
                        return

                # 获取选中的运营商
                selected_operators = [op for op, var in self.operator_vars.items() if var.get()]
                operators_text = ", ".join(selected_operators) if selected_operators else "全部"

                save_data = {
                    'numbers': self.generated_numbers,
                    'count': len(self.generated_numbers),
                    'save_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'operator': operators_text,
                    'generation_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'version': '1.0'
                }

                with open(filename, 'wb') as f:
                    pickle.dump(save_data, f)

                messagebox.showinfo("保存成功",
                                    f"号码已保存到: {filename}\n共保存 {len(self.generated_numbers):,} 个号码")
            except PermissionError:
                messagebox.showerror("保存失败", "没有文件写入权限，请选择其他位置")
            except OSError as e:
                messagebox.showerror("保存失败", f"文件系统错误: {str(e)}")
            except Exception as e:
                messagebox.showerror("保存失败", f"保存文件时出错: {str(e)}")

    def check_disk_space(self, filename, count):
        """检查磁盘空间"""
        try:
            # 估算文件大小
            estimated_size = count * 20 + 1024  # 每个号码约20字节 + 1KB元数据

            if hasattr(os, 'statvfs'):  # Unix-like
                stat = os.statvfs(os.path.dirname(filename))
                free_space = stat.f_bavail * stat.f_frsize
            else:  # Windows
                import ctypes
                free_bytes = ctypes.c_ulonglong(0)
                ctypes.windll.kernel32.GetDiskFreeSpaceExW(
                    ctypes.c_wchar_p(os.path.dirname(filename)),
                    None, None, ctypes.pointer(free_bytes))
                free_space = free_bytes.value

            return free_space > estimated_size * 2  # 保留2倍空间
        except:
            return True  # 如果检查失败，假设空间足够

    def load_numbers(self):
        """从二进制文件读取号码"""
        filename = filedialog.askopenfilename(
            title="打开号码文件",
            filetypes=[("电话本文件", "*.bin"), ("所有文件", "*.*")]
        )

        if filename:
            try:
                # 检查文件大小
                file_size = os.path.getsize(filename)
                if file_size > 100 * 1024 * 1024:  # 100MB限制
                    if not messagebox.askyesno("文件过大", "文件较大（>100MB），加载可能较慢，是否继续？"):
                        return

                with open(filename, 'rb') as f:
                    load_data = pickle.load(f)

                # 验证数据完整性
                is_valid, message = self.validate_file_data(load_data)
                if not is_valid:
                    messagebox.showerror("文件错误", message)
                    return

                # 内存安全检查
                is_safe, mem_message = self.check_memory_safe(load_data['count'])
                if not is_safe:
                    if not messagebox.askyesno("内存警告", f"{mem_message}，是否继续加载？"):
                        return

                self.generated_numbers = load_data['numbers']
                self.results_text.delete(1.0, tk.END)

                # 分批显示
                display_count = min(len(self.generated_numbers), 1000)
                for i, number in enumerate(self.generated_numbers[:display_count], 1):
                    self.results_text.insert(tk.END, f"[{i}] {number}\n")

                if len(self.generated_numbers) > display_count:
                    self.results_text.insert(tk.END,
                                             f"\n... 还有 {len(self.generated_numbers) - display_count} 个号码未显示，导出为文本查看完整内容。\n")

                # 显示文件信息
                self.results_text.insert(tk.END, f"\n=== 文件信息 ===\n")
                self.results_text.insert(tk.END, f"号码数量: {load_data['count']:,}\n")
                self.results_text.insert(tk.END, f"保存时间: {load_data.get('save_time', '未知')}\n")
                self.results_text.insert(tk.END, f"运营商: {load_data.get('operator', '未知')}\n")
                self.results_text.insert(tk.END, f"生成时间: {load_data.get('generation_time', '未知')}\n")
                self.results_text.insert(tk.END, f"加载时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

                # 更新统计信息
                self.stats_label.config(text=f"已加载: {len(self.generated_numbers):,} 个号码")

                messagebox.showinfo("加载成功", f"已从文件加载 {len(self.generated_numbers):,} 个号码")

            except (pickle.UnpicklingError, EOFError, KeyError) as e:
                messagebox.showerror("文件错误", "文件格式不正确或已损坏")
            except PermissionError:
                messagebox.showerror("加载失败", "没有文件读取权限")
            except Exception as e:
                messagebox.showerror("加载失败", f"读取文件时出错: {str(e)}")

    def export_numbers(self):
        """导出号码为文本文件"""
        if not self.generated_numbers:
            messagebox.showwarning("无数据", "没有可导出的号码数据！")
            return

        default_filename = self.get_default_filename(".txt")

        filename = filedialog.asksaveasfilename(
            title="导出号码文本",
            defaultextension=".txt",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")],
            initialfile=default_filename
        )

        if filename:
            try:
                # 检查磁盘空间
                estimated_size = len(self.generated_numbers) * 15 + 1024
                if not self.check_disk_space(filename, estimated_size):
                    if not messagebox.askyesno("磁盘空间警告", "磁盘空间可能不足，是否继续导出？"):
                        return

                # 获取选中的运营商
                selected_operators = [op for op, var in self.operator_vars.items() if var.get()]
                operators_text = ", ".join(selected_operators) if selected_operators else "全部"

                with open(filename, 'w', encoding='utf-8') as f:
                    f.write("手机号码列表\n")
                    f.write("=" * 40 + "\n")
                    f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"号码数量: {len(self.generated_numbers):,}\n")
                    f.write(f"运营商: {operators_text}\n")
                    f.write("=" * 40 + "\n\n")

                    for i, number in enumerate(self.generated_numbers, 1):
                        f.write(f"{i}. {number}\n")
                        # 分批写入，避免内存问题
                        if i % 1000 == 0:
                            f.flush()

                messagebox.showinfo("导出成功", f"号码已导出到: {filename}")
            except Exception as e:
                messagebox.showerror("导出失败", f"导出文件时出错: {str(e)}")

    def clear_results(self):
        """清空结果并释放内存"""
        self.results_text.delete(1.0, tk.END)
        self.count_spinbox.delete(0, tk.END)
        self.count_spinbox.insert(0, "10")
        self.generated_numbers = []  # 释放内存
        self.stats_label.config(text="已生成: 0 个号码")
        self.status_var.set("就绪")
        self.progress['value'] = 0
        self.count_spinbox.focus_set()

    def cleanup(self):
        """清理资源"""
        self.stop_generation()
        self.generated_numbers = []  # 释放内存
        import gc
        gc.collect()

    def exit_program(self):
        """安全退出程序"""
        if self.is_generating:
            if messagebox.askyesno("确认退出", "号码生成正在进行中，确定要退出吗？"):
                self.cleanup()
                self.root.after(1000, self.root.destroy)
        else:
            if messagebox.askyesno("确认退出", "确定要退出程序吗？"):
                self.cleanup()
                self.root.quit()
                self.root.destroy()


def main():
    try:
        root = tk.Tk()
        app = PhoneNumberGenerator(root)
        root.mainloop()
    except Exception as e:
        messagebox.showerror("启动错误", f"程序启动失败: {str(e)}")
        print(f"启动错误: {traceback.format_exc()}")


if __name__ == "__main__":
    main()