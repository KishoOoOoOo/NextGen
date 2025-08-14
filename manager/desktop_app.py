#!/usr/bin/env python3
"""
NextGen Hub - Desktop Application
Advanced Process Management System for Windows
Supports Arabic and English languages
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import time
import json
import requests
import webbrowser
from datetime import datetime
import subprocess
import sys
import os
from pathlib import Path
import locale

# Add backend to path
sys.path.append(str(Path(__file__).parent / "backend"))

from backend.process_manager import ProcessManager
from backend.project_store import ProjectStore
from backend.orchestrator import Orchestrator
from backend.models import ProjectConfig, HealthcheckConfig, RestartPolicy

# Language support
class LanguageManager:
    def __init__(self):
        self.current_language = 'ar'  # Default to Arabic
        self.translations = {
            'ar': {
                'title': 'NextGen Hub - مدير العمليات المتقدم',
                'projects': 'المشاريع',
                'overview': 'نظرة عامة',
                'logs': 'السجلات',
                'metrics': 'المقاييس',
                'status': 'الحالة',
                'running': 'يعمل',
                'stopped': 'متوقف',
                'error': 'خطأ',
                'healthy': 'سليم',
                'unhealthy': 'غير سليم',
                'start': 'تشغيل',
                'stop': 'إيقاف',
                'restart': 'إعادة تشغيل',
                'edit': 'تعديل',
                'delete': 'حذف',
                'add_project': 'إضافة مشروع',
                'refresh': 'تحديث',
                'web_dashboard': 'لوحة المراقبة الويب',
                'language': 'اللغة',
                'english': 'English',
                'arabic': 'العربية',
                'project_name': 'اسم المشروع',
                'working_dir': 'مجلد العمل',
                'command': 'الأمر',
                'args': 'المعاملات',
                'instances': 'عدد النسخ',
                'port': 'المنفذ',
                'description': 'الوصف',
                'save': 'حفظ',
                'cancel': 'إلغاء',
                'confirm_delete': 'هل أنت متأكد من حذف هذا المشروع؟',
                'delete_title': 'تأكيد الحذف',
                'server_starting': 'جاري بدء الخادم...',
                'server_running': 'الخادم يعمل',
                'server_stopped': 'الخادم متوقف',
                'cpu_usage': 'استخدام المعالج',
                'memory_usage': 'استخدام الذاكرة',
                'uptime': 'وقت التشغيل',
                'restart_count': 'عدد إعادات التشغيل',
                'ready': 'جاهز',
                'current_status': 'الحالة الحالية',
                'project_information': 'معلومات المشروع',
            },
            'en': {
                'title': 'NextGen Hub - Advanced Process Manager',
                'projects': 'Projects',
                'overview': 'Overview',
                'logs': 'Logs',
                'metrics': 'Metrics',
                'status': 'Status',
                'running': 'Running',
                'stopped': 'Stopped',
                'error': 'Error',
                'healthy': 'Healthy',
                'unhealthy': 'Unhealthy',
                'start': 'Start',
                'stop': 'Stop',
                'restart': 'Restart',
                'edit': 'Edit',
                'delete': 'Delete',
                'add_project': 'Add Project',
                'refresh': 'Refresh',
                'web_dashboard': 'Web Dashboard',
                'language': 'Language',
                'english': 'English',
                'arabic': 'العربية',
                'project_name': 'Project Name',
                'working_dir': 'Working Directory',
                'command': 'Command',
                'args': 'Arguments',
                'instances': 'Instances',
                'port': 'Port',
                'description': 'Description',
                'save': 'Save',
                'cancel': 'Cancel',
                'confirm_delete': 'Are you sure you want to delete this project?',
                'delete_title': 'Confirm Delete',
                'server_starting': 'Starting server...',
                'server_running': 'Server Running',
                'server_stopped': 'Server Stopped',
                'cpu_usage': 'CPU Usage',
                'memory_usage': 'Memory Usage',
                'uptime': 'Uptime',
                'restart_count': 'Restart Count',
                'ready': 'Ready',
                'current_status': 'Current Status',
                'project_information': 'Project Information',
            }
        }
    
    def get(self, key):
        return self.translations[self.current_language].get(key, key)
    
    def set_language(self, lang):
        self.current_language = lang


class NextGenDesktop:
    def __init__(self):
        self.root = tk.Tk()
        
        # Initialize language manager
        self.lang = LanguageManager()
        
        self.root.title(self.lang.get('title'))
        self.root.geometry("1400x900")
        self.root.configure(bg='#0f172a')
        
        # Set window icon (NextGen logo)
        try:
            # Try to load icon if available
            icon_path = Path(__file__).parent / "static" / "nextgen_icon.ico"
            if icon_path.exists():
                self.root.iconbitmap(str(icon_path))
        except:
            pass
        
        # Initialize backend components
        from backend.project_store import default_store_path
        from pathlib import Path
        
        self.store = ProjectStore(default_store_path())
        runtime_dir = Path("data/runtime")
        self.process_manager = ProcessManager(runtime_dir)
        self.orchestrator = None
        
        # Server process
        self.server_process = None
        self.server_running = False
        
        # Data
        self.projects = []
        self.selected_project = None
        
        # Setup UI
        self.setup_styles()
        self.create_widgets()
        self.setup_layout()
        
        # Start backend server
        self.start_backend_server()
        
        # Start data refresh
        self.refresh_data()
        
        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def setup_styles(self):
        """Setup custom styles for the application"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure colors
        style.configure('Title.TLabel', 
                       background='#0f172a', 
                       foreground='#f8fafc', 
                       font=('Segoe UI', 16, 'bold'))
        
        style.configure('Subtitle.TLabel', 
                       background='#0f172a', 
                       foreground='#cbd5e1', 
                       font=('Segoe UI', 10))
        
        style.configure('Status.TLabel', 
                       background='#1e293b', 
                       foreground='#f8fafc', 
                       font=('Segoe UI', 9))
        
        style.configure('Custom.Treeview',
                       background='#1e293b',
                       foreground='#f8fafc',
                       fieldbackground='#1e293b',
                       borderwidth=0)
        
        style.configure('Custom.Treeview.Heading',
                       background='#334155',
                       foreground='#f8fafc',
                       font=('Segoe UI', 9, 'bold'))
        
        style.configure('Success.TButton',
                       background='#10b981',
                       foreground='white',
                       font=('Segoe UI', 9, 'bold'))
        
        style.configure('Danger.TButton',
                       background='#ef4444',
                       foreground='white',
                       font=('Segoe UI', 9, 'bold'))
        
        style.configure('Warning.TButton',
                       background='#f59e0b',
                       foreground='white',
                       font=('Segoe UI', 9, 'bold'))
    
    def create_widgets(self):
        """Create all UI widgets"""
        # Main container
        self.main_frame = tk.Frame(self.root, bg='#0f172a')
        
        # Header
        self.header_frame = tk.Frame(self.main_frame, bg='#1e293b', height=80)
        self.header_frame.pack_propagate(False)
        
        # Title
        title_label = ttk.Label(self.header_frame, 
                               text="🚀 NextGen Hub", 
                               style='Title.TLabel')
        title_label.pack(side=tk.LEFT, padx=20, pady=20)
        
        # Subtitle
        subtitle_label = ttk.Label(self.header_frame, 
                                  text="Advanced Process Management System", 
                                  style='Subtitle.TLabel')
        subtitle_label.pack(side=tk.LEFT, padx=(0, 20), pady=25)
        
        # Language selector
        self.lang_frame = tk.Frame(self.header_frame, bg='#1e293b')
        self.lang_frame.pack(side=tk.RIGHT, padx=(0, 10), pady=20)
        
        ttk.Label(self.lang_frame, text=self.lang.get('language'), 
                 style='Subtitle.TLabel').pack(side=tk.LEFT, padx=5)
        
        self.lang_var = tk.StringVar(value=self.lang.current_language)
        self.lang_combo = ttk.Combobox(self.lang_frame, textvariable=self.lang_var,
                                      values=['ar', 'en'], state='readonly', width=8)
        self.lang_combo.pack(side=tk.LEFT, padx=5)
        self.lang_combo.bind('<<ComboboxSelected>>', self.change_language)
        
        # Control buttons
        self.control_frame = tk.Frame(self.header_frame, bg='#1e293b')
        self.control_frame.pack(side=tk.RIGHT, padx=20, pady=20)
        
        self.web_btn = ttk.Button(self.control_frame, 
                                 text=f"🌐 {self.lang.get('web_dashboard')}", 
                                 command=self.open_web_dashboard)
        self.web_btn.pack(side=tk.LEFT, padx=5)
        
        self.refresh_btn = ttk.Button(self.control_frame, 
                                     text=f"🔄 {self.lang.get('refresh')}", 
                                     command=self.refresh_data)
        self.refresh_btn.pack(side=tk.LEFT, padx=5)
        
        self.add_btn = ttk.Button(self.control_frame, 
                                 text=f"➕ {self.lang.get('add_project')}", 
                                 command=self.show_add_project_dialog,
                                 style='Success.TButton')
        self.add_btn.pack(side=tk.LEFT, padx=5)
        
        # Content area
        self.content_frame = tk.Frame(self.main_frame, bg='#0f172a')
        
        # Left panel - Project list
        self.left_panel = tk.Frame(self.content_frame, bg='#1e293b', width=500)
        self.left_panel.pack_propagate(False)
        
        # Project list header
        list_header = tk.Frame(self.left_panel, bg='#334155', height=40)
        list_header.pack(fill=tk.X)
        list_header.pack_propagate(False)
        
        ttk.Label(list_header, text=f"📋 {self.lang.get('projects')}", 
                 style='Title.TLabel').pack(side=tk.LEFT, padx=15, pady=10)
        
        # Project treeview
        self.tree_frame = tk.Frame(self.left_panel, bg='#1e293b')
        self.tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Treeview with scrollbar
        self.tree = ttk.Treeview(self.tree_frame, 
                                style='Custom.Treeview',
                                columns=('status', 'cpu', 'memory'),
                                show='tree headings')
        
        self.tree.heading('#0', text='Project Name')
        self.tree.heading('status', text='Status')
        self.tree.heading('cpu', text='CPU %')
        self.tree.heading('memory', text='Memory MB')
        
        self.tree.column('#0', width=200)
        self.tree.column('status', width=80)
        self.tree.column('cpu', width=80)
        self.tree.column('memory', width=100)
        
        # Scrollbar for treeview
        tree_scroll = ttk.Scrollbar(self.tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scroll.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind selection event
        self.tree.bind('<<TreeviewSelect>>', self.on_project_select)
        
        # Right panel - Project details
        self.right_panel = tk.Frame(self.content_frame, bg='#1e293b')
        
        # Details header
        details_header = tk.Frame(self.right_panel, bg='#334155', height=40)
        details_header.pack(fill=tk.X)
        details_header.pack_propagate(False)
        
        ttk.Label(details_header, text="📊 Project Details", 
                 style='Title.TLabel').pack(side=tk.LEFT, padx=15, pady=10)
        
        # Project actions
        self.actions_frame = tk.Frame(details_header, bg='#334155')
        self.actions_frame.pack(side=tk.RIGHT, padx=15, pady=5)
        
        self.start_btn = ttk.Button(self.actions_frame, 
                                   text="▶️ Start", 
                                   command=self.start_project,
                                   style='Success.TButton')
        self.start_btn.pack(side=tk.LEFT, padx=2)
        
        self.stop_btn = ttk.Button(self.actions_frame, 
                                  text="⏹️ Stop", 
                                  command=self.stop_project,
                                  style='Danger.TButton')
        self.stop_btn.pack(side=tk.LEFT, padx=2)
        
        self.restart_btn = ttk.Button(self.actions_frame, 
                                     text="🔄 Restart", 
                                     command=self.restart_project,
                                     style='Warning.TButton')
        self.restart_btn.pack(side=tk.LEFT, padx=2)
        
        self.edit_btn = ttk.Button(self.actions_frame, 
                                  text="✏️ Edit", 
                                  command=self.edit_project)
        self.edit_btn.pack(side=tk.LEFT, padx=2)
        
        self.delete_btn = ttk.Button(self.actions_frame, 
                                    text="🗑️ Delete", 
                                    command=self.delete_project,
                                    style='Danger.TButton')
        self.delete_btn.pack(side=tk.LEFT, padx=2)
        
        # Details content
        self.details_content = tk.Frame(self.right_panel, bg='#1e293b')
        self.details_content.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.details_content)
        
        # Overview tab
        self.overview_frame = tk.Frame(self.notebook, bg='#1e293b')
        self.notebook.add(self.overview_frame, text='Overview')
        
        # Logs tab
        self.logs_frame = tk.Frame(self.notebook, bg='#1e293b')
        self.notebook.add(self.logs_frame, text='Logs')
        
        # Metrics tab
        self.metrics_frame = tk.Frame(self.notebook, bg='#1e293b')
        self.notebook.add(self.metrics_frame, text='Metrics')
        
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Setup tab contents
        self.setup_overview_tab()
        self.setup_logs_tab()
        self.setup_metrics_tab()
        
        # Status bar
        self.status_bar = tk.Frame(self.main_frame, bg='#334155', height=30)
        self.status_bar.pack_propagate(False)
        
        self.status_label = ttk.Label(self.status_bar, 
                                     text=self.lang.get('ready'), 
                                     style='Status.TLabel')
        self.status_label.pack(side=tk.LEFT, padx=10, pady=5)
        
        # Server status
        self.server_status_label = ttk.Label(self.status_bar, 
                                            text=f"{self.lang.get('server_running')}" if self.server_running else self.lang.get('server_starting'), 
                                            style='Status.TLabel')
        self.server_status_label.pack(side=tk.RIGHT, padx=10, pady=5)
    
    def setup_overview_tab(self):
        """Setup the overview tab content"""
        # Project info frame
        info_frame = tk.LabelFrame(self.overview_frame, 
                                  text=self.lang.get('project_information'), 
                                  bg='#1e293b', 
                                  fg='#f8fafc',
                                  font=('Segoe UI', 10, 'bold'))
        info_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.info_text = scrolledtext.ScrolledText(info_frame, 
                                                  height=8, 
                                                  bg='#334155', 
                                                  fg='#f8fafc',
                                                  font=('Consolas', 9))
        self.info_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Status frame
        status_frame = tk.LabelFrame(self.overview_frame, 
                                   text=self.lang.get('current_status'), 
                                   bg='#1e293b', 
                                   fg='#f8fafc',
                                   font=('Segoe UI', 10, 'bold'))
        status_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.status_text = scrolledtext.ScrolledText(status_frame, 
                                                    height=6, 
                                                    bg='#334155', 
                                                    fg='#f8fafc',
                                                    font=('Consolas', 9))
        self.status_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    def setup_logs_tab(self):
        """Setup the logs tab content"""
        # Logs control frame
        logs_control = tk.Frame(self.logs_frame, bg='#1e293b')
        logs_control.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(logs_control, 
                  text=f"🔄 {self.lang.get('refresh_logs')}", 
                  command=self.refresh_logs).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(logs_control, 
                  text=f"🗑️ {self.lang.get('clear_logs')}", 
                  command=self.clear_logs).pack(side=tk.LEFT, padx=5)
        
        # Logs display
        self.logs_text = scrolledtext.ScrolledText(self.logs_frame, 
                                                  bg='#0f172a', 
                                                  fg='#f8fafc',
                                                  font=('Consolas', 9),
                                                  wrap=tk.WORD)
        self.logs_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
    
    def setup_metrics_tab(self):
        """Setup the metrics tab content"""
        # Metrics display
        self.metrics_text = scrolledtext.ScrolledText(self.metrics_frame, 
                                                     bg='#334155', 
                                                     fg='#f8fafc',
                                                     font=('Consolas', 9))
        self.metrics_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    def change_language(self, event=None):
        """Change the application language"""
        new_lang = self.lang_var.get()
        # Skip if no actual change
        if new_lang == self.lang.current_language:
            return
        self.lang.set_language(new_lang)
        # Destroy the entire main frame to avoid stacking/offset issues
        try:
            if hasattr(self, 'main_frame') and self.main_frame.winfo_exists():
                self.main_frame.destroy()
        except Exception:
            pass
        # Recreate UI with the new language
        self.create_widgets()
        self.setup_layout()
        self.root.title(self.lang.get('title'))
        # Refresh data to repopulate views
        self.refresh_data()
    
    def setup_layout(self):
        """Setup the main layout"""
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        self.header_frame.pack(fill=tk.X)
        self.content_frame.pack(fill=tk.BOTH, expand=True)
        self.left_panel.pack(side=tk.LEFT, fill=tk.Y)
        self.right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM)
    
    def start_backend_server(self):
        """Start the backend server in a separate thread"""
        def run_server():
            try:
                import uvicorn
                from backend.app import app
                
                # Start server
                uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")
            except Exception as e:
                print(f"Failed to start server: {e}")
        
        # Start server in thread
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        
        # Update status after delay
        self.root.after(3000, self.check_server_status)
    
    def check_server_status(self):
        """Check if the server is running"""
        try:
            response = requests.get("http://127.0.0.1:8000/api/projects", timeout=2)
            if response.status_code == 200:
                self.server_running = True
                self.server_status_label.config(text="Server: Running ✅")
            else:
                self.server_status_label.config(text="Server: Error ❌")
        except:
            self.server_status_label.config(text="Server: Not Running ❌")
            # Retry after 5 seconds
            self.root.after(5000, self.check_server_status)
    
    def refresh_data(self):
        """Refresh project data"""
        try:
            # Load projects from store
            self.projects = []
            for p in self.store.list_projects():
                # Update status and collect metrics
                updated_project = self.process_manager.status(p)
                if updated_project.runtime.status == "running":
                    updated_project = self.process_manager.collect_metrics(updated_project)
                self.projects.append(updated_project)
            self.update_project_list()
            self.status_label.config(text=f"{self.lang.get('ready')}: {len(self.projects)}")
            if self.selected_project:
                # Keep selection consistent by id
                sel_id = self.selected_project.config.id
                for proj in self.projects:
                    if proj.config.id == sel_id:
                        self.selected_project = proj
                        break
                self.update_project_details()
        except Exception as e:
            self.status_label.config(text=f"Error loading projects: {e}")
        # Schedule next refresh
        self.root.after(5000, self.refresh_data)
    
    def update_project_list(self):
        """Update the project list in the treeview"""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        # Add projects
        for project in self.projects:
            status = project.runtime.status
            cpu = f"{project.runtime.metrics.cpu_percent:.1f}" if project.runtime.metrics else "0.0"
            memory = f"{project.runtime.metrics.memory_rss_mb:.1f}" if project.runtime.metrics else "0.0"
            status_emoji = {
                'running': '🟢',
                'stopped': '🔴',
                'error': '🟠',
                'starting': '🟡',
                'unhealthy': '🟡',
                'crashed': '🔴'
            }.get(status, '⚪')
            # Health indicator
            health_emoji = ""
            if project.runtime.health:
                if project.runtime.health.status == "healthy":
                    health_emoji = "✅"
                elif project.runtime.health.status == "unhealthy":
                    health_emoji = "⚠️"
                else:
                    health_emoji = "❓"
            # Use iid as project id to retrieve later
            self.tree.insert('', 'end', iid=project.config.id,
                             text=f"{status_emoji} {project.config.name} {health_emoji}",
                             values=(status, cpu, memory))
    
    def on_project_select(self, event):
        """Handle project selection"""
        selection = self.tree.selection()
        if selection:
            item_id = selection[0]  # iid is project id
            self.selected_project = next((p for p in self.projects if p.config.id == item_id), None)
            if self.selected_project:
                self.update_project_details()
    
    def update_project_details(self):
        """Update the project details panel"""
        if not self.selected_project:
            return
        project = self.selected_project
        info = f"""Project ID: {project.config.id}
Name: {project.config.name}
Command: {project.config.command}
Working Directory: {project.config.working_dir}
Arguments: {' '.join(project.config.args) if project.config.args else 'None'}
Instances: {project.config.instances}
Log Path: {project.config.log_path or 'Default'}
Ports: {', '.join(map(str, project.config.ports)) if project.config.ports else 'None'}
Description: {project.config.description or 'No description'}

Environment Variables:
{chr(10).join([f'  {k}={v}' for k, v in project.config.env.items()]) if project.config.env else '  None'}

Healthcheck:
  Type: {project.config.healthcheck.type if project.config.healthcheck else 'None'}
  Interval: {project.config.healthcheck.interval_seconds if project.config.healthcheck else 'N/A'}s
  Timeout: {project.config.healthcheck.timeout_seconds if project.config.healthcheck else 'N/A'}s

Restart Policy:
  Auto Restart: {project.config.restart_policy.autorestart if project.config.restart_policy else 'No'}
  Max Restarts: {project.config.restart_policy.max_restarts_per_hour if project.config.restart_policy else 'N/A'}
  Delay: {project.config.restart_policy.restart_delay_seconds if project.config.restart_policy else 'N/A'}s"""
        self.info_text.delete(1.0, tk.END)
        self.info_text.insert(1.0, info)
        uptime_str = "N/A"
        if project.runtime.metrics and project.runtime.metrics.uptime_seconds:
            hours = int(project.runtime.metrics.uptime_seconds // 3600)
            minutes = int((project.runtime.metrics.uptime_seconds % 3600) // 60)
            uptime_str = f"{hours}h {minutes}m"
        status_info = f"""Status: {project.runtime.status}
Health: {project.runtime.health.status if project.runtime.health else 'Unknown'}
PIDs: {', '.join(map(str, project.runtime.pids)) if project.runtime.pids else 'None'}
Uptime: {uptime_str}
Restarts: {project.runtime.restarts_total}
Last Started: {project.runtime.started_at.strftime('%Y-%m-%d %H:%M:%S') if project.runtime.started_at else 'Never'}
Last Stopped: {project.runtime.stopped_at.strftime('%Y-%m-%d %H:%M:%S') if project.runtime.stopped_at else 'Never'}

Metrics:
  CPU: {project.runtime.metrics.cpu_percent:.2f}%
  Memory: {project.runtime.metrics.memory_rss_mb:.2f} MB ({project.runtime.metrics.memory_percent:.2f}%)
  Threads: {project.runtime.metrics.threads}
  Memory VMS: {project.runtime.metrics.memory_vms_mb:.2f} MB"""
        self.status_text.delete(1.0, tk.END)
        self.status_text.insert(1.0, status_info)
        if project.runtime.metrics:
            metrics_info = f"""Performance Metrics:

CPU Usage: {project.runtime.metrics.cpu_percent:.2f}%
Memory Usage: {project.runtime.metrics.memory_rss_mb:.2f} MB
Memory Percentage: {project.runtime.metrics.memory_percent:.2f}%
Memory VMS: {project.runtime.metrics.memory_vms_mb:.2f} MB
Thread Count: {project.runtime.metrics.threads}
Uptime: {uptime_str}

Process Information:
PIDs: {', '.join(map(str, project.runtime.pids)) if project.runtime.pids else 'None'}
Status: {project.runtime.status}
Health Status: {project.runtime.health.status if project.runtime.health else 'Unknown'}

Restart Statistics:
Total Restarts: {project.runtime.restarts_total}
Last Restart: {project.runtime.started_at.strftime('%Y-%m-%d %H:%M:%S') if project.runtime.started_at else 'Never'}

System Information:
Working Directory: {project.config.working_dir}
Command: {project.config.command} {' '.join(project.config.args) if project.config.args else ''}
Instances: {project.config.instances}"""
        else:
            metrics_info = "No metrics available - project may not be running"
        self.metrics_text.delete(1.0, tk.END)
        self.metrics_text.insert(1.0, metrics_info)
        self.refresh_logs()
    
    def refresh_logs(self):
        """Refresh project logs"""
        if not self.selected_project:
            return
        
        try:
            if self.server_running:
                response = requests.get(f"http://127.0.0.1:8000/api/projects/{self.selected_project.config.id}/logs")
                if response.status_code == 200:
                    logs_data = response.json()
                    logs_content = '\n'.join(logs_data.get('logs', []))
                else:
                    logs_content = "Failed to fetch logs from server"
            else:
                logs_content = "Server not running - cannot fetch logs"
        except Exception as e:
            logs_content = f"Error fetching logs: {e}"
        
        self.logs_text.delete(1.0, tk.END)
        self.logs_text.insert(1.0, logs_content)
        self.logs_text.see(tk.END)
    
    def clear_logs(self):
        """Clear the logs display"""
        self.logs_text.delete(1.0, tk.END)
    
    def start_project(self):
        """Start the selected project"""
        if not self.selected_project:
            messagebox.showwarning("Warning", "Please select a project first")
            return
        try:
            if self.server_running:
                response = requests.post(f"http://127.0.0.1:8000/api/projects/{self.selected_project.config.id}/start")
                if response.status_code == 200:
                    messagebox.showinfo("Success", f"Project '{self.selected_project.config.name}' started successfully")
                    self.refresh_data()
                else:
                    messagebox.showerror("Error", f"Failed to start project: {response.text}")
            else:
                self.process_manager.start(self.selected_project)
                messagebox.showinfo("Success", f"Project '{self.selected_project.config.name}' started successfully")
                self.refresh_data()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start project: {e}")
    
    def stop_project(self):
        """Stop the selected project"""
        if not self.selected_project:
            messagebox.showwarning("Warning", "Please select a project first")
            return
        try:
            if self.server_running:
                response = requests.post(f"http://127.0.0.1:8000/api/projects/{self.selected_project.config.id}/stop")
                if response.status_code == 200:
                    messagebox.showinfo("Success", f"Project '{self.selected_project.config.name}' stopped successfully")
                    self.refresh_data()
                else:
                    messagebox.showerror("Error", f"Failed to stop project: {response.text}")
            else:
                self.process_manager.stop(self.selected_project)
                messagebox.showinfo("Success", f"Project '{self.selected_project.config.name}' stopped successfully")
                self.refresh_data()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to stop project: {e}")
    
    def restart_project(self):
        """Restart the selected project"""
        if not self.selected_project:
            messagebox.showwarning("Warning", "Please select a project first")
            return
        try:
            if self.server_running:
                response = requests.post(f"http://127.0.0.1:8000/api/projects/{self.selected_project.config.id}/restart")
                if response.status_code == 200:
                    messagebox.showinfo("Success", f"Project '{self.selected_project.config.name}' restarted successfully")
                    self.refresh_data()
                else:
                    messagebox.showerror("Error", f"Failed to restart project: {response.text}")
            else:
                self.process_manager.restart(self.selected_project)
                messagebox.showinfo("Success", f"Project '{self.selected_project.config.name}' restarted successfully")
                self.refresh_data()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to restart project: {e}")
    
    def edit_project(self):
        """Edit the selected project"""
        if not self.selected_project:
            messagebox.showwarning("Warning", "Please select a project first")
            return
        
        self.show_project_dialog(self.selected_project)
    
    def delete_project(self):
        """Delete the selected project"""
        if not self.selected_project:
            messagebox.showwarning("Warning", "Please select a project first")
            return
        
        if messagebox.askyesno(self.lang.get('delete_title'), 
                              f"{self.lang.get('confirm_delete')} '{self.selected_project.config.name}'?"):
            try:
                self.store.delete_project(self.selected_project.config.id)
                messagebox.showinfo("Success", f"Project '{self.selected_project.config.name}' deleted successfully")
                self.selected_project = None
                self.refresh_data()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete project: {e}")
    
    def show_add_project_dialog(self):
        """Show dialog to add a new project"""
        self.show_project_dialog()
    
    def show_project_dialog(self, project=None):
        """Show project creation/editing dialog"""
        dialog = ProjectDialog(self.root, project, self.store)
        if dialog.result:
            self.refresh_data()
    
    def open_web_dashboard(self):
        """Open the web dashboard in browser"""
        if self.server_running:
            webbrowser.open("http://127.0.0.1:8000/dashboard")
        else:
            messagebox.showwarning("Warning", "Server is not running. Please wait for it to start.")
    
    def on_closing(self):
        """Handle application closing"""
        if messagebox.askokcancel("Quit", "Do you want to quit OrchestratorX Pro?"):
            self.root.destroy()
    
    def run(self):
        """Run the application"""
        self.root.mainloop()


class ProjectDialog:
    def __init__(self, parent, project=None, store=None):
        self.parent = parent
        self.project = project
        self.store = store
        self.result = None
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Edit Project" if project else "Add Project")
        self.dialog.geometry("600x700")
        self.dialog.configure(bg='#1e293b')
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self.create_form()
        
        # Center dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (self.dialog.winfo_width() // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")
        
        self.dialog.wait_window()
    
    def create_form(self):
        """Create the project form"""
        # Main frame
        main_frame = tk.Frame(self.dialog, bg='#1e293b')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Title
        title = tk.Label(main_frame, 
                        text="Edit Project" if self.project else "Add New Project",
                        bg='#1e293b', 
                        fg='#f8fafc',
                        font=('Segoe UI', 14, 'bold'))
        title.pack(pady=(0, 20))
        
        # Form fields
        self.create_field(main_frame, "Project ID:", "id")
        self.create_field(main_frame, "Name:", "name")
        self.create_field(main_frame, "Working Directory:", "working_dir")
        self.create_field(main_frame, "Command:", "command")
        self.create_field(main_frame, "Arguments (space-separated):", "args")
        self.create_field(main_frame, "Instances:", "instances")
        self.create_field(main_frame, "Log Path:", "log_path")
        self.create_field(main_frame, "Ports (comma-separated):", "ports")
        self.create_field(main_frame, "Description:", "description")
        
        # Environment variables
        env_frame = tk.LabelFrame(main_frame, 
                                 text="Environment Variables", 
                                 bg='#1e293b', 
                                 fg='#f8fafc',
                                 font=('Segoe UI', 10, 'bold'))
        env_frame.pack(fill=tk.X, pady=10)
        
        self.env_text = scrolledtext.ScrolledText(env_frame, 
                                                 height=4, 
                                                 bg='#334155', 
                                                 fg='#f8fafc',
                                                 font=('Consolas', 9))
        self.env_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Buttons
        button_frame = tk.Frame(main_frame, bg='#1e293b')
        button_frame.pack(fill=tk.X, pady=20)
        
        tk.Button(button_frame, 
                 text="Cancel", 
                 command=self.cancel,
                 bg='#64748b', 
                 fg='white',
                 font=('Segoe UI', 10, 'bold'),
                 padx=20).pack(side=tk.RIGHT, padx=5)
        
        tk.Button(button_frame, 
                 text="Save", 
                 command=self.save,
                 bg='#10b981', 
                 fg='white',
                 font=('Segoe UI', 10, 'bold'),
                 padx=20).pack(side=tk.RIGHT, padx=5)
        
        # Load existing data if editing
        if self.project:
            self.load_project_data()
    
    def create_field(self, parent, label_text, field_name):
        """Create a form field"""
        frame = tk.Frame(parent, bg='#1e293b')
        frame.pack(fill=tk.X, pady=5)
        
        label = tk.Label(frame, 
                        text=label_text, 
                        bg='#1e293b', 
                        fg='#f8fafc',
                        font=('Segoe UI', 10),
                        width=20, 
                        anchor='w')
        label.pack(side=tk.LEFT)
        
        entry = tk.Entry(frame, 
                        bg='#334155', 
                        fg='#f8fafc',
                        font=('Segoe UI', 10),
                        insertbackground='#f8fafc')
        entry.pack(side=tk.RIGHT, fill=tk.X, expand=True)
        
        setattr(self, f"{field_name}_entry", entry)
    
    def load_project_data(self):
        """Load existing project data into form"""
        self.id_entry.insert(0, self.project.config.id)
        self.name_entry.insert(0, self.project.config.name)
        self.working_dir_entry.insert(0, self.project.config.working_dir)
        self.command_entry.insert(0, self.project.config.command)
        self.args_entry.insert(0, ' '.join(self.project.config.args) if self.project.config.args else '')
        self.instances_entry.insert(0, str(self.project.config.instances))
        self.log_path_entry.insert(0, self.project.config.log_path or '')
        self.ports_entry.insert(0, ','.join(map(str, self.project.config.ports)) if self.project.config.ports else '')
        self.description_entry.insert(0, self.project.config.description or '')
        
        # Environment variables
        if self.project.config.env:
            env_text = '\n'.join([f"{k}={v}" for k, v in self.project.config.env.items()])
            self.env_text.insert(1.0, env_text)
    
    def save(self):
        """Save the project"""
        try:
            # Get form data
            project_id = self.id_entry.get().strip()
            name = self.name_entry.get().strip()
            working_dir = self.working_dir_entry.get().strip()
            command = self.command_entry.get().strip()
            args_str = self.args_entry.get().strip()
            instances_str = self.instances_entry.get().strip()
            log_path = self.log_path_entry.get().strip()
            ports_str = self.ports_entry.get().strip()
            description = self.description_entry.get().strip()
            
            # Validate required fields
            if not all([project_id, name, working_dir, command]):
                messagebox.showerror("Error", "Please fill in all required fields")
                return
            
            # Verify working directory exists
            if not Path(working_dir).exists():
                messagebox.showerror("Error", f"Working directory does not exist: {working_dir}")
                return
            
            # Parse fields
            args = args_str.split() if args_str else []
            instances = int(instances_str) if instances_str else 1
            ports = [int(p.strip()) for p in ports_str.split(',') if p.strip()] if ports_str else []
            
            # Parse environment variables
            env = {}
            env_text = self.env_text.get(1.0, tk.END).strip()
            if env_text:
                for line in env_text.split('\n'):
                    if '=' in line:
                        key, value = line.split('=', 1)
                        env[key.strip()] = value.strip()
            
            # Create project config
            project_config = ProjectConfig(
                id=project_id,
                name=name,
                working_dir=working_dir,
                command=command,
                args=args,
                instances=instances,
                log_path=log_path if log_path else None,
                ports=ports,
                description=description if description else None,
                env=env
            )
            
            # Save project
            self.store.upsert_project(project_config)
            self.result = project_config
            
            messagebox.showinfo("Success", f"Project '{name}' saved successfully")
            self.dialog.destroy()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save project: {e}")
    
    def cancel(self):
        """Cancel dialog"""
        self.dialog.destroy()


if __name__ == "__main__":
    app = NextGenDesktop()
    app.run()


def main():
    """Main entry point for the desktop application"""
    app = NextGenDesktop()
    app.run()


if __name__ == "__main__":
    main()