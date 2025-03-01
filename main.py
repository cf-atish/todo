import sys
import json
import os
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QEvent, Signal, QSize
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                               QListWidget, QLineEdit, QPushButton, QHBoxLayout,
                               QListWidgetItem, QMessageBox, QGraphicsDropShadowEffect, QLabel)
from PySide6.QtGui import QColor, QPalette

class GlassMemo(QMainWindow):
    def __init__(self):
        super().__init__()

        # 设置数据文件路径
        self.data_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'memo_data.json')

        # 窗口基础设置
        self.setWindowTitle("Glass Memo")
        self.resize(600, 800)

        # 创建标题栏（用于拖动）
        self.title_bar = QWidget()
        self.title_bar.setFixedHeight(40)
        self.title_bar.setCursor(Qt.OpenHandCursor)
        self.title_bar.setStyleSheet("background: rgba(60, 60, 60, 0.5); border-radius: 10px;")
        self.title_bar.installEventFilter(self)

        # 添加标题文字和任务统计
        title_layout = QHBoxLayout(self.title_bar)
        title_layout.setContentsMargins(15, 0, 10, 0)
        
        # 左侧标题和统计信息容器
        left_container = QWidget()
        left_layout = QHBoxLayout(left_container)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(10)
        
        # title_label = QLineEdit("玻璃备忘录")
        # title_label.setReadOnly(True)
        # title_label.setStyleSheet("""
        #     QLineEdit {
        #         background: transparent;
        #         border: none;
        #         font-size: 18px;
        #         font-weight: bold;
        #         font-family: "Microsoft YaHei";
        #     }
        # """)
        
        # 添加任务统计标签
        self.stats_label = QLineEdit("(待办:0 完成:0 取消:0)")
        self.stats_label.setReadOnly(True)
        self.stats_label.setFixedWidth(200)
        self.stats_label.setStyleSheet("""
            QLineEdit {
                background: transparent;
                border: none;
                color: white;
                font-size: 14px;
                font-family: "Microsoft YaHei";
            }
        """)

        # 添加展开/折叠按钮
        self.toggle_btn = QPushButton("▼")  # 初始为展开状态
        self.toggle_btn.setFixedSize(30, 30)
        self.toggle_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: white;
                font-size: 16px;
                border: none;
            }
            QPushButton:hover {
                background: rgba(100, 100, 100, 0.5);
                border-radius: 15px;
            }
            QPushButton:pressed {
                background: rgba(80, 80, 80, 0.7);
            }
        """)
        self.toggle_btn.clicked.connect(self.toggle_content)

        # 关闭按钮
        close_btn = QPushButton("×")
        close_btn.setFixedSize(40, 40)
        close_btn.clicked.connect(self.close)
        close_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: white;
                font-size: 24px;
                border: none;
            }
            QPushButton:hover {
                background: rgba(255, 80, 80, 0.7);
                border-radius: 15px;
            }
            QPushButton:pressed {
                background: rgba(255, 50, 50, 0.9);
            }
        """)
        
        # left_layout.addWidget(title_label)
        left_layout.addWidget(self.stats_label)
        
        title_layout.addWidget(left_container)
        title_layout.addWidget(self.toggle_btn)
        title_layout.addStretch()
        title_layout.addWidget(close_btn)

        # 窗口拖动相关变量
        self.dragging = False
        self.offset = None

        # 创建主控件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 10, 20, 20)
        main_layout.setSpacing(15)

        # 添加标题栏
        main_layout.addWidget(self.title_bar)

        # 输入区域（增加项目）
        self.input_layout = QHBoxLayout()
        self.input_layout.setSpacing(10)

        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("输入备忘内容...")
        self.input_field.setMinimumHeight(40)
        self.input_field.setStyleSheet("""
            QLineEdit {
                background: rgba(50, 50, 50, 0.7);
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 10px;
                color: white;
                padding: 10px 15px;
                font-size: 16px;
            }
            QLineEdit:placeholder {
                color: rgba(255, 255, 255, 0.5);
            }
        """)
        self.input_field.setFocus()  # 自动聚焦
        self.input_layout.addWidget(self.input_field)

        self.add_btn = QPushButton("添加任务")
        self.add_btn.setFixedSize(100, 40)
        self.add_btn.setStyleSheet("""
            QPushButton {
                background: rgba(80, 160, 80, 0.7);
                border: none;
                border-radius: 10px;
                color: white;
                font-size: 15px;
            }
            QPushButton:hover {
                background: rgba(100, 180, 100, 0.8);
            }
            QPushButton:pressed {
                background: rgba(60, 140, 60, 0.9);
            }
        """)
        self.input_layout.addWidget(self.add_btn)

        self.clear_btn = QPushButton("清空")
        self.clear_btn.setFixedSize(80, 40)
        self.clear_btn.setStyleSheet("""
            QPushButton {
                background: rgba(200, 60, 60, 0.7);
                border: none;
                border-radius: 10px;
                color: white;
                font-size: 15px;
            }
            QPushButton:hover {
                background: rgba(220, 70, 70, 0.8);
            }
            QPushButton:pressed {
                background: rgba(180, 50, 50, 0.9);
            }
        """)
        self.input_layout.addWidget(self.clear_btn)

        # 将输入区域包装为 QWidget 以便控制可见性
        self.input_layout_widget = QWidget()
        self.input_layout_widget.setLayout(self.input_layout)

        # 备忘录列表（展示项目）
        self.memo_list = QListWidget()
        self.memo_list.setAlternatingRowColors(True)
        self.memo_list.setStyleSheet("""
            QListWidget {
                background: rgba(40, 40, 40, 0.8);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 12px;
                color: white;
                font-size: 16px;
                padding: 10px;
            }
            QListWidget::item {
                background: rgba(60, 60, 60, 0.7);
                border-radius: 10px;
                margin: 6px 2px;
                padding: 5px;
            }
            QListWidget::item:hover {
                background: rgba(70, 70, 70, 0.8);
            }
        """)
        self.memo_list.setDragEnabled(True)
        self.memo_list.setAcceptDrops(True)
        self.memo_list.setDefaultDropAction(Qt.MoveAction)

        # 组装界面
        main_layout.addWidget(self.input_layout_widget)
        main_layout.addWidget(self.memo_list)

        # 设置窗口特效
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # Windows 亚克力效果处理
        try:
            if sys.platform == "win32":
                from PySide6.QtWinExtras import QtWin
                QtWin.enableBlurBehindWindow(self)
        except ImportError:
            self.setAttribute(Qt.WA_TranslucentBackground)
            self.setWindowOpacity(0.98)

        # 连接信号
        self.add_btn.clicked.connect(self.add_memo)
        self.clear_btn.clicked.connect(self.clear_all)
        self.input_field.returnPressed.connect(self.add_memo)  # Enter 键添加任务

        # 初始化动画
        self.fade_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_animation.setDuration(1000)
        self.fade_animation.setStartValue(0)
        self.fade_animation.setEndValue(1)
        self.fade_animation.setEasingCurve(QEasingCurve.InOutQuad)
        self.fade_animation.start()

        # 添加阴影效果
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 100))
        shadow.setOffset(0, 5)
        central_widget.setGraphicsEffect(shadow)

        # 设置消息框样式
        QMessageBox.setStyleSheet(self, """
            QMessageBox {
                background: rgba(50, 50, 50, 0.9);
                border-radius: 10px;
            }
            QMessageBox QLabel {
                color: white;
                font-size: 14px;
                padding: 10px;
            }
            QMessageBox QPushButton {
                width: 60px;
                padding: 8px 15px;
                margin: 5px;
                border-radius: 8px;
                color: white;
                font-size: 14px;
                background: rgba(70, 70, 70, 0.7);
                border: none;
            }
            QMessageBox QPushButton:hover {
                background: rgba(90, 90, 90, 0.8);
            }
        """)

        # 初始化内容可见性
        self.is_content_visible = True
        self.input_layout_widget.setVisible(self.is_content_visible)
        self.memo_list.setVisible(self.is_content_visible)

        # 加载保存的数据
        self.load_data()

    def load_data(self):
        """从文件加载数据"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    tasks = json.load(f)
                    for task in tasks:
                        item = QListWidgetItem()
                        task_widget = TaskItemWidget(task['text'])
                        task_widget.status = task['status']
                        task_widget.change_status(task['status'])
                        item.setSizeHint(task_widget.sizeHint())
                        self.memo_list.addItem(item)
                        self.memo_list.setItemWidget(item, task_widget)
                        task_widget.delete_btn.clicked.connect(lambda: self.delete_item(item))
                        task_widget.status_changed.connect(self.sort_memos)
                    self.update_stats()
        except Exception as e:
            print(f"加载数据出错: {e}")

    def save_data(self):
        """保存数据到文件"""
        try:
            tasks = []
            for i in range(self.memo_list.count()):
                item = self.memo_list.item(i)
                widget = self.memo_list.itemWidget(item)
                tasks.append({
                    'text': widget.text_label.text(),
                    'status': widget.status
                })
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(tasks, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存数据出错: {e}")

    def closeEvent(self, event):
        """窗口关闭时保存数据"""
        reply = QMessageBox.question(
            self,
            "确认退出",
            "确定要退出程序吗？\n您的数据将会被保存。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.save_data()
            super().closeEvent(event)
        else:
            event.ignore()  # 取消关闭

    def toggle_content(self):
        """切换内容的显示和隐藏"""
        self.is_content_visible = not self.is_content_visible
        self.input_layout_widget.setVisible(self.is_content_visible)
        self.memo_list.setVisible(self.is_content_visible)
        
        # 创建动画
        self.resize_animation = QPropertyAnimation(self, b"size")
        self.resize_animation.setDuration(300)  # 300毫秒的动画时长
        self.resize_animation.setEasingCurve(QEasingCurve.InOutQuad)
        
        if self.is_content_visible:
            self.resize_animation.setEndValue(QSize(600, 800))  # 显示内容时恢复原始大小
            self.toggle_btn.setText("▼")  # 展开状态
        else:
            self.resize_animation.setEndValue(QSize(600, 60))   # 隐藏内容时仅显示标题栏高度
            self.toggle_btn.setText("▲")  # 折叠状态
            
        self.resize_animation.start()

    def eventFilter(self, obj, event):
        """事件过滤器，仅处理标题栏的拖动"""
        if obj == self.title_bar:
            if event.type() == QEvent.MouseButtonPress:
                if event.button() == Qt.LeftButton:
                    # 左键按下，开始拖动
                    self.dragging = True
                    self.offset = event.globalPosition().toPoint() - self.pos()
                    obj.setCursor(Qt.ClosedHandCursor)
                    return True
            elif event.type() == QEvent.MouseMove:
                if self.dragging and event.buttons() & Qt.LeftButton:
                    # 拖动窗口
                    self.move(event.globalPosition().toPoint() - self.offset)
                    return True
            elif event.type() == QEvent.MouseButtonRelease:
                if event.button() == Qt.LeftButton:
                    # 左键释放，结束拖动
                    self.dragging = False
                    obj.setCursor(Qt.OpenHandCursor)
                    return True
        return super().eventFilter(obj, event)

    def update_stats(self):
        """更新任务统计信息"""
        todo_count = 0
        complete_count = 0
        cancel_count = 0
        
        for i in range(self.memo_list.count()):
            item = self.memo_list.item(i)
            widget = self.memo_list.itemWidget(item)
            if widget.status == "todo":
                todo_count += 1
            elif widget.status == "complete":
                complete_count += 1
            elif widget.status == "cancel":
                cancel_count += 1
                
        self.stats_label.setText(f"(待办:{todo_count} 完成:{complete_count} 取消:{cancel_count})")

    def add_memo(self):
        """添加备忘录项"""
        text = self.input_field.text()
        if text.strip():
            item = QListWidgetItem()
            task_widget = TaskItemWidget(text)
            item.setSizeHint(task_widget.sizeHint())
            self.memo_list.addItem(item)
            self.memo_list.setItemWidget(item, task_widget)
            task_widget.delete_btn.clicked.connect(lambda: self.delete_item(item))
            task_widget.status_changed.connect(self.sort_memos)
            self.sort_memos()  # 添加后排序
            self.update_stats()  # 更新统计
            self.input_field.clear()
            self.save_data()  # 保存数据

    def clear_all(self):
        """清空所有备忘录项"""
        if self.memo_list.count() == 0:
            return
        reply = QMessageBox.question(
            self,
            "确认清空",
            "确定要清空所有任务吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.memo_list.clear()
            self.update_stats()  # 更新统计
            self.save_data()  # 保存数据

    def delete_item(self, item):
        """删除指定备忘录项"""
        self.memo_list.takeItem(self.memo_list.row(item))
        self.sort_memos()  # 删除后排序
        self.update_stats()  # 更新统计
        self.save_data()  # 保存数据

    def sort_memos(self):
        """对备忘录项按状态排序"""
        tasks = []
        for i in range(self.memo_list.count()):
            item = self.memo_list.item(i)
            widget = self.memo_list.itemWidget(item)
            tasks.append({
                'text': widget.text_label.text(),
                'status': widget.status
            })
        
        self.memo_list.clear()
        unfinished = [task for task in tasks if task['status'] in ["todo"]]
        finished = [task for task in tasks if task['status'] in ["complete", "cancel"]]
        sorted_tasks = unfinished + finished
        
        for task in sorted_tasks:
            item = QListWidgetItem()
            task_widget = TaskItemWidget(task['text'])
            task_widget.status = task['status']
            task_widget.change_status(task['status'])
            item.setSizeHint(task_widget.sizeHint())
            self.memo_list.addItem(item)
            self.memo_list.setItemWidget(item, task_widget)
            task_widget.delete_btn.clicked.connect(lambda: self.delete_item(item))
            task_widget.status_changed.connect(self.sort_memos)
        self.update_stats()  # 更新统计
        self.save_data()  # 保存数据

class TaskItemWidget(QWidget):
    status_changed = Signal()  # 当状态改变时发出信号

    def __init__(self, text, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)

        # 任务文本
        self.text_label = QLineEdit(text)
        self.text_label.setReadOnly(True)
        self.text_label.setMinimumHeight(50)
        self.text_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.text_label.setStyleSheet("""
            QLineEdit {
                border: none;
                background: transparent;
                color: white;
                font-size: 18px;
                padding: 5px;
                margin-bottom: 10px;
            }
        """)

        # 按钮行
        btn_container = QWidget()
        btn_container.setFixedHeight(50)
        btn_layout = QHBoxLayout(btn_container)
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.setSpacing(10)

        # 四个按钮
        self.todo_btn = QPushButton("代办📋")
        self.complete_btn = QPushButton("完成✅")
        self.cancel_btn = QPushButton("取消❌")
        self.delete_btn = QPushButton("删除🗑️")
        self.currentstatus = QLabel("当前状态：代办")
        self.currentstatus.setStyleSheet("background: transparent;color: white;")
        # 设置按钮大小
        for btn in [self.todo_btn, self.complete_btn, self.cancel_btn, self.delete_btn]:
            btn.setFixedSize(80, 40)

        # 设置按钮样式
        button_style = """
            QPushButton {
                background: transparent;
                color: white;
                border: none;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.1);
                border-radius: 5px;
            }
            QPushButton:pressed {
                background: rgba(255, 255, 255, 0.2);
            }
            QPushButton:focus {
                outline: none;
            }
        """
        
        self.todo_btn.setStyleSheet(button_style)
        self.complete_btn.setStyleSheet(button_style)
        self.cancel_btn.setStyleSheet(button_style)
        self.delete_btn.setStyleSheet(button_style)
        
        # 设置状态标签样式
        self.currentstatus.setStyleSheet("""
            QLabel {
                background: transparent;
                color: white;
            }
            QLabel:focus {
                outline: none;
            }
        """)

        # 连接信号
        self.todo_btn.clicked.connect(lambda: self.change_status("todo"))
        self.complete_btn.clicked.connect(lambda: self.change_status("complete"))
        self.cancel_btn.clicked.connect(lambda: self.change_status("cancel"))
        
        btn_layout.addWidget(self.todo_btn)
        btn_layout.addWidget(self.complete_btn)
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(self.delete_btn)
        btn_layout.addWidget(self.currentstatus)
        # 添加到主布局
        layout.addWidget(self.text_label)
        layout.addWidget(btn_container)

        self.status = "todo"  # 初始状态
        self.change_status("todo")

    def change_status(self, status):
        """更改任务状态并更新样式"""
        self.status = status
        style = """
            QLineEdit {
                border: none;
                background: %s;
                font-size: 18px;
                padding: 5px;
                margin-bottom: 10px;
                border-radius: 5px;
                color: white;
            }
        """
        if status == "todo":
            self.text_label.setStyleSheet(style % "rgba(255, 255, 0, 0.2)")
            self.currentstatus.setText("当前状态：代办")
        elif status == "complete":
            self.text_label.setStyleSheet(style % "rgba(0, 255, 0, 0.2)")
            self.currentstatus.setText("当前状态：完成")
        elif status == "cancel":
            self.text_label.setStyleSheet(style % "rgba(255, 0, 0, 0.2)")
            self.currentstatus.setText("当前状态：取消")
        self.status_changed.emit()  # 通知状态改变
        
        # 更新父窗口的统计信息
        parent = self.window()
        if isinstance(parent, GlassMemo):
            parent.update_stats()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # 设置调色板保持一致的视觉效果
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(53, 53, 53))
    app.setPalette(palette)
    
    window = GlassMemo()
    window.show()
    sys.exit(app.exec())