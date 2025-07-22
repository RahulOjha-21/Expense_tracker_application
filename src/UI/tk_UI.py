import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, ttk, messagebox, simpledialog
import os
import threading
import queue
import sqlite3
import logging
from datetime import datetime
from PIL import Image, ImageTk
from pdf2image import convert_from_path
import json
import sys
from pathlib import Path

# Add the src directory to the Python path
src_path = str(Path(__file__).resolve().parent.parent)
if src_path not in sys.path:
    sys.path.append(src_path)

# Assuming other necessary imports from your project are here
from core.processor import get_image_data, extract_json_data
from utils.db_manager import save_to_sqlite_db, clear_db_data, browse_db_data, CREATE_TABLE_QUERY
import pandas as pd
import shutil
import subprocess
from utils.logger import setup_logger

try:
    import openpyxl
except ImportError:
    messagebox.showerror("Error", "The openpyxl module is required to export data to XLSX. Please install it using 'pip install openpyxl'.")

# Custom logger handler that redirects log messages to the UI
class QueueHandler(logging.Handler):
    def __init__(self, log_queue):
        super().__init__()
        self.log_queue = log_queue

    def emit(self, record):
        self.log_queue.put(self.format(record))

logger = setup_logger()

# --- ENHANCED SETTINGS WINDOW ---
class SettingsWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent.root)
        self.title("⚙️ Application Settings")
        self.geometry("650x400")
        self.transient(parent.root)
        self.grab_set()  # Make window modal
        
        self.parent = parent
        self.configure_window()
        self.create_enhanced_ui()
        self.load_settings()
        
    def configure_window(self):
        # Center the window
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (650 // 2)
        y = (self.winfo_screenheight() // 2) - (400 // 2)
        self.geometry(f"650x400+{x}+{y}")
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
    def create_enhanced_ui(self):
        # Header frame with gradient-like appearance
        header_frame = ctk.CTkFrame(self, height=80, corner_radius=0, fg_color=("#1f538d", "#144870"))
        header_frame.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        header_frame.grid_propagate(False)
        header_frame.grid_columnconfigure(0, weight=1)
        
        title_label = ctk.CTkLabel(
            header_frame,
            text="⚙️ Application Configuration",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color="white"
        )
        title_label.grid(row=0, column=0, pady=20)
        
        subtitle_label = ctk.CTkLabel(
            header_frame,
            text="Configure your application paths and preferences",
            font=ctk.CTkFont(size=12),
            text_color=("#E0E0E0", "#B0B0B0")
        )
        subtitle_label.grid(row=1, column=0, pady=(0, 10))
        
        # Main content frame
        content_frame = ctk.CTkFrame(self, corner_radius=0)
        content_frame.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)
        content_frame.grid_columnconfigure(1, weight=1)
        
        # Source folder section
        source_section = ctk.CTkFrame(content_frame, corner_radius=10)
        source_section.grid(row=0, column=0, columnspan=3, sticky="ew", padx=30, pady=(30, 15))
        source_section.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(
            source_section,
            text="📁 Source Directory",
            font=ctk.CTkFont(size=16, weight="bold")
        ).grid(row=0, column=0, columnspan=3, padx=20, pady=(15, 5), sticky="w")
        
        ctk.CTkLabel(
            source_section,
            text="Select the folder containing images and PDFs to analyze",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        ).grid(row=1, column=0, columnspan=3, padx=20, pady=(0, 10), sticky="w")
        
        self.source_path_entry = ctk.CTkEntry(
            source_section,
            placeholder_text="Choose source folder path...",
            font=ctk.CTkFont(size=11),
            height=35
        )
        self.source_path_entry.grid(row=2, column=0, columnspan=2, padx=20, pady=(0, 20), sticky="ew")
        
        browse_source_btn = ctk.CTkButton(
            source_section,
            text="Browse",
            command=self.browse_source,
            width=80,
            height=35,
            font=ctk.CTkFont(size=11, weight="bold")
        )
        browse_source_btn.grid(row=2, column=2, padx=(10, 20), pady=(0, 20))
        
        # Database section
        db_section = ctk.CTkFrame(content_frame, corner_radius=10)
        db_section.grid(row=1, column=0, columnspan=3, sticky="ew", padx=30, pady=15)
        db_section.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(
            db_section,
            text="🗄️ Database Location",
            font=ctk.CTkFont(size=16, weight="bold")
        ).grid(row=0, column=0, columnspan=3, padx=20, pady=(15, 5), sticky="w")
        
        ctk.CTkLabel(
            db_section,
            text="Specify where to store the application database file",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        ).grid(row=1, column=0, columnspan=3, padx=20, pady=(0, 10), sticky="w")
        
        self.db_path_entry = ctk.CTkEntry(
            db_section,
            placeholder_text="Choose database file location...",
            font=ctk.CTkFont(size=11),
            height=35
        )
        self.db_path_entry.grid(row=2, column=0, columnspan=2, padx=20, pady=(0, 20), sticky="ew")
        
        browse_db_btn = ctk.CTkButton(
            db_section,
            text="Browse",
            command=self.browse_db,
            width=80,
            height=35,
            font=ctk.CTkFont(size=11, weight="bold")
        )
        browse_db_btn.grid(row=2, column=2, padx=(10, 20), pady=(0, 20))
        
        # Action buttons
        button_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        button_frame.grid(row=2, column=0, columnspan=3, pady=30, sticky="ew")
        button_frame.grid_columnconfigure((0, 1), weight=1)
        
        cancel_btn = ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=self.destroy,
            fg_color="transparent",
            border_width=2,
            text_color=("gray10", "gray90"),
            border_color=("gray70", "gray30"),
            width=120,
            height=40,
            font=ctk.CTkFont(size=12, weight="bold")
        )
        cancel_btn.grid(row=0, column=0, padx=(0, 10), sticky="e")
        
        save_btn = ctk.CTkButton(
            button_frame,
            text="💾 Save Configuration",
            command=self.save_and_close,
            width=180,
            height=40,
            font=ctk.CTkFont(size=12, weight="bold")
        )
        save_btn.grid(row=0, column=1, padx=(10, 0), sticky="w")

    def browse_source(self):
        path = filedialog.askdirectory(title="Select Source Directory")
        if path: 
            self.source_path_entry.delete(0, "end")
            self.source_path_entry.insert(0, path)

    def browse_db(self):
        path = filedialog.asksaveasfilename(
            title="Select or Create Database File", 
            defaultextension=".db",
            filetypes=[("Database files", "*.db"), ("All files", "*.*")]
        )
        if path: 
            self.db_path_entry.delete(0, "end")
            self.db_path_entry.insert(0, path)

    def load_settings(self):
        self.source_path_entry.insert(0, self.parent.source_path)
        self.db_path_entry.insert(0, self.parent.db_path)

    def save_and_close(self):
        self.parent.source_path = self.source_path_entry.get()
        self.parent.db_path = self.db_path_entry.get()
        self.parent.save_app_settings()
        self.parent.update_paths_in_ui()
        self.destroy()

# --- ENHANCED MAIN UI ---
class ImageAnalyzerUI:
    def __init__(self, root):
        self.root = root
        self.root.title("💼 Expense Tracker AI - Professional Edition")
        self.root.geometry("1900x1080")
        
        # Set up modern theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")
        
        # Configure window
        self.configure_main_window()
        
        # Initialize logging queue and setup logger
        self.log_queue = queue.Queue()
        self.setup_logger()
        
        # Load settings and create UI
        self.load_app_settings()
        self.create_enhanced_ui()
        
        # Start consuming logs
        self.consume_logs()

        # Set default paths
        self.source_path_var.set(os.path.join(os.getcwd(), "inputs"))
        self.db_path_var.set(os.path.join(os.getcwd(), "outputs", "DB", "image_data.db"))

        # Configure and load data
        self.configure_treeview_style()
        self.load_data_from_db(self.db_path_var.get())
        
        # Initialize log panel state
        self.log_minimized = False
        
    def configure_main_window(self):
        # Center window on screen
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (1900 // 2)
        y = (self.root.winfo_screenheight() // 2) - (1080 // 2)
        self.root.geometry(f"1900x1080+{x}+{y}")
        
        # Configure grid weights - FIXED VERSION for better accessibility
        self.root.grid_columnconfigure(0, weight=0, minsize=380)  # Left panel - fixed width
        self.root.grid_columnconfigure(1, weight=1)              # Center panel - expandable
        self.root.grid_columnconfigure(2, weight=0, minsize=450) # Right panel - fixed width
        self.root.grid_rowconfigure(0, weight=3)                 # Main panels - 3/4 of space
        self.root.grid_rowconfigure(1, weight=1)                 # Log panel - 1/4 of space

    def load_app_settings(self):
        try:
            with open("config/app_settings.json", "r") as f:
                settings = json.load(f)
                self.source_path = settings.get("source_path", os.path.join(os.getcwd(), "inputs"))
                self.db_path = settings.get("db_path", os.path.join(os.getcwd(), "outputs", "DB", "image_data.db"))
        except (FileNotFoundError, json.JSONDecodeError):
            self.source_path = os.path.join(os.getcwd(), "inputs")
            self.db_path = os.path.join(os.getcwd(), "outputs", "DB", "image_data.db")
    
    def save_app_settings(self):
        os.makedirs("config", exist_ok=True)
        settings = {"source_path": self.source_path, "db_path": self.db_path}
        with open("config/app_settings.json", "w") as f:
            json.dump(settings, f, indent=4)

    def create_enhanced_ui(self):
        # === Enhanced Left Control Panel ===
        self.control_panel = ctk.CTkScrollableFrame(self.root, corner_radius=15, width=360)
        self.control_panel.grid(row=0, column=0, sticky="nsew", padx=(15, 7), pady=15)
        self.create_enhanced_control_panel()

        # === Enhanced Center Data Panel ===
        self.data_panel = ctk.CTkFrame(self.root, corner_radius=15)
        self.data_panel.grid(row=0, column=1, sticky="nsew", padx=7, pady=15)
        self.create_enhanced_data_panel()

        # === Enhanced Right Preview Panel ===
        self.preview_panel = ctk.CTkFrame(self.root, corner_radius=15)
        self.preview_panel.grid(row=0, column=2, sticky="nsew", padx=(7, 15), pady=15)
        self.create_enhanced_preview_panel()
        
        # === Enhanced Bottom Log Panel ===
        self.log_panel = ctk.CTkFrame(self.root, corner_radius=15)
        self.log_panel.grid(row=1, column=0, columnspan=3, sticky="nsew", padx=15, pady=(0, 15))
        self.create_enhanced_log_panel()

    def create_enhanced_control_panel(self):
        # Control panel is now scrollable, so no need for complex grid management
        
        # Header with gradient-like appearance
        header_frame = ctk.CTkFrame(self.control_panel, height=70, corner_radius=10, 
                                  fg_color=("#1f538d", "#144870"))
        header_frame.pack(fill="x", padx=15, pady=15)
        
        ctk.CTkLabel(
            header_frame,
            text="🎛️ Control Center",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="white"
        ).pack(pady=20)

        # Configuration Section
        config_frame = ctk.CTkFrame(self.control_panel, corner_radius=10)
        config_frame.pack(fill="x", padx=15, pady=(0, 15))
        
        ctk.CTkLabel(
            config_frame,
            text="📋 Configuration",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(pady=(15, 10), padx=15, anchor="w")
        
        # Source Path
        ctk.CTkLabel(
            config_frame,
            text="📁 Source Directory:",
            font=ctk.CTkFont(size=11, weight="bold"),
            anchor="w"
        ).pack(fill="x", padx=15, pady=(5, 2))
        
        self.source_path_var = tk.StringVar()
        source_entry = ctk.CTkEntry(
            config_frame,
            textvariable=self.source_path_var,
            placeholder_text="Select source folder...",
            font=ctk.CTkFont(size=10)
        )
        source_entry.pack(fill="x", padx=15, pady=(0, 5))
        
        browse_source_btn = ctk.CTkButton(
            config_frame,
            text="📂 Browse Source",
            command=self.browse_source,
            height=32,
            font=ctk.CTkFont(size=10, weight="bold")
        )
        browse_source_btn.pack(fill="x", padx=15, pady=(0, 10))

        # DB Path
        ctk.CTkLabel(
            config_frame,
            text="🗄️ Database File:",
            font=ctk.CTkFont(size=11, weight="bold"),
            anchor="w"
        ).pack(fill="x", padx=15, pady=(5, 2))
        
        self.db_path_var = tk.StringVar()
        db_entry = ctk.CTkEntry(
            config_frame,
            textvariable=self.db_path_var,
            placeholder_text="Select database file...",
            font=ctk.CTkFont(size=10)
        )
        db_entry.pack(fill="x", padx=15, pady=(0, 5))
        
        browse_db_btn = ctk.CTkButton(
            config_frame,
            text="🗃️ Browse Database",
            command=self.browse_db,
            height=32,
            font=ctk.CTkFont(size=10, weight="bold")
        )
        browse_db_btn.pack(fill="x", padx=15, pady=(0, 15))

        # Enhanced Statistics Panel
        stats_frame = ctk.CTkFrame(self.control_panel, corner_radius=10)
        stats_frame.pack(fill="x", padx=15, pady=(0, 15))
        
        # Statistics Header
        header_stats = ctk.CTkFrame(stats_frame, height=45, corner_radius=8, 
                                  fg_color=("#2b7d32", "#1b5e20"))
        header_stats.pack(fill="x", padx=10, pady=10)
        
        stats_title_frame = ctk.CTkFrame(header_stats, fg_color="transparent")
        stats_title_frame.pack(expand=True, fill="both")
        
        ctk.CTkLabel(
            stats_title_frame,
            text="📊 Analytics Dashboard",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="white"
        ).pack(pady=10)

        # Statistics content with modern cards
        stats_content = ctk.CTkFrame(stats_frame, fg_color="transparent")
        stats_content.pack(fill="x", padx=10, pady=(0, 15))
        
        # Records card
        records_card = ctk.CTkFrame(stats_content, corner_radius=8)
        records_card.pack(fill="x", pady=3)
        
        records_inner = ctk.CTkFrame(records_card, fg_color="transparent")
        records_inner.pack(fill="x", padx=10, pady=8)
        
        ctk.CTkLabel(records_inner, text="📄", font=ctk.CTkFont(size=20)).pack(side="left")
        self.total_records_label = ctk.CTkLabel(
            records_inner,
            text="Total Records: 0",
            font=ctk.CTkFont(size=11, weight="bold"),
            anchor="w"
        )
        self.total_records_label.pack(side="left", padx=(10, 0), fill="x", expand=True)
        
        # Amount card
        amount_card = ctk.CTkFrame(stats_content, corner_radius=8)
        amount_card.pack(fill="x", pady=3)
        
        amount_inner = ctk.CTkFrame(amount_card, fg_color="transparent")
        amount_inner.pack(fill="x", padx=10, pady=8)
        
        ctk.CTkLabel(amount_inner, text="💰", font=ctk.CTkFont(size=20)).pack(side="left")
        self.total_amount_label = ctk.CTkLabel(
            amount_inner,
            text="Total Amount: ₹0.00",
            font=ctk.CTkFont(size=11, weight="bold"),
            anchor="w"
        )
        self.total_amount_label.pack(side="left", padx=(10, 0), fill="x", expand=True)
        
        # Date range card
        date_card = ctk.CTkFrame(stats_content, corner_radius=8)
        date_card.pack(fill="x", pady=3)
        
        date_inner = ctk.CTkFrame(date_card, fg_color="transparent")
        date_inner.pack(fill="x", padx=10, pady=8)
        
        ctk.CTkLabel(date_inner, text="📅", font=ctk.CTkFont(size=20)).pack(side="left")
        self.date_range_label = ctk.CTkLabel(
            date_inner,
            text="Date Range: N/A",
            font=ctk.CTkFont(size=11, weight="bold"),
            anchor="w"
        )
        self.date_range_label.pack(side="left", padx=(10, 0), fill="x", expand=True)

        # Enhanced Action Buttons
        actions_frame = ctk.CTkFrame(self.control_panel, corner_radius=10)
        actions_frame.pack(fill="x", padx=15, pady=(0, 15))
        
        ctk.CTkLabel(
            actions_frame,
            text="🚀 Actions",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(pady=(15, 10), padx=15, anchor="w")
        
        # Primary action button
        self.start_button = ctk.CTkButton(
            actions_frame,
            text="▶️ Start Analysis",
            command=self.start_analysis,
            height=45,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=("#2e7d32", "#1b5e20"),
            hover_color=("#43a047", "#2e7d32")
        )
        self.start_button.pack(fill="x", pady=5, padx=15)
        
        # Progress Bar with enhanced styling
        progress_container = ctk.CTkFrame(actions_frame, fg_color="transparent", height=30)
        progress_container.pack(fill="x", padx=15, pady=5)
        
        self.progress_bar = ctk.CTkProgressBar(
            progress_container,
            height=8,
            corner_radius=4
        )
        self.progress_bar.pack(fill="x", pady=10)
        self.progress_bar.set(0)
        
        # Secondary action buttons
        self.export_button = ctk.CTkButton(
            actions_frame,
            text="📊 Export to CSV",
            command=self.export_to_csv,
            height=38,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=("#1976d2", "#0d47a1"),
            hover_color=("#1e88e5", "#1565c0")
        )
        self.export_button.pack(fill="x", pady=3, padx=15)

        self.export_files_button = ctk.CTkButton(
            actions_frame,
            text="📁 Export Files",
            command=self.export_files,
            height=38,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=("#f57c00", "#e65100"),
            hover_color=("#ff9800", "#f57c00")
        )
        self.export_files_button.pack(fill="x", pady=3, padx=15)

        self.delete_button = ctk.CTkButton(
            actions_frame,
            text="🗑️ Delete Selected",
            command=self.delete_selected,
            height=38,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=("#d32f2f", "#b71c1c"),
            hover_color=("#f44336", "#d32f2f")
        )
        self.delete_button.pack(fill="x", pady=3, padx=15)

        # Add some spacing
        spacer = ctk.CTkFrame(actions_frame, height=10, fg_color="transparent")
        spacer.pack(fill="x", pady=5)

        # Settings button at bottom
        self.settings_button = ctk.CTkButton(
            self.control_panel,
            text="⚙️ Application Settings",
            command=self.open_settings_window,
            height=40,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="transparent",
            border_width=2,
            text_color=("gray10", "gray90"),
            border_color=("gray70", "gray30")
        )
        self.settings_button.pack(fill="x", pady=15, padx=15)

    def create_enhanced_data_panel(self):
        self.data_panel.grid_rowconfigure(1, weight=1)
        self.data_panel.grid_columnconfigure(0, weight=1)
        
        # Enhanced header
        header_frame = ctk.CTkFrame(self.data_panel, height=60, corner_radius=0, 
                                  fg_color=("#1f538d", "#144870"))
        header_frame.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        header_frame.grid_propagate(False)
        header_frame.grid_columnconfigure(0, weight=1)
        
        header_content = ctk.CTkFrame(header_frame, fg_color="transparent")
        header_content.pack(expand=True, fill="both", padx=20)
        
        ctk.CTkLabel(
            header_content,
            text="💼 Expense Records Database",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="white"
        ).pack(side="left", pady=15)
        
        # Search functionality
        search_frame = ctk.CTkFrame(header_content, fg_color="transparent")
        search_frame.pack(side="right", pady=12)
        
        self.search_entry = ctk.CTkEntry(
            search_frame,
            placeholder_text="🔍 Search records...",
            width=200,
            height=35,
            font=ctk.CTkFont(size=11)
        )
        self.search_entry.pack(side="right", padx=(10, 0))

        # Enhanced tree container
        tree_container = ctk.CTkFrame(self.data_panel, corner_radius=0)
        tree_container.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)
        tree_container.grid_columnconfigure(0, weight=1)
        tree_container.grid_rowconfigure(0, weight=1)

        # Create treeview with enhanced styling
        self.tree = ttk.Treeview(
            tree_container,
            columns=("ID", "Amount", "Date", "Original Path", "Renamed", "Category", "Tags"),
            show="headings",
            height=20
        )
        self.tree.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)

        # Enhanced scrollbars
        v_scrollbar = ctk.CTkScrollbar(
            tree_container,
            orientation="vertical",
            command=self.tree.yview
        )
        v_scrollbar.grid(row=0, column=1, sticky="ns", padx=(0, 20), pady=20)
        self.tree.configure(yscrollcommand=v_scrollbar.set)
        
        h_scrollbar = ctk.CTkScrollbar(
            tree_container,
            orientation="horizontal",
            command=self.tree.xview
        )
        h_scrollbar.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 20))
        self.tree.configure(xscrollcommand=h_scrollbar.set)

        # Configure columns
        self.tree.heading("ID", text="ID", anchor="center")
        self.tree.heading("Amount", text="💰 Amount", anchor="center")
        self.tree.heading("Date", text="📅 Date", anchor="center")
        self.tree.heading("Original Path", text="📄 Original Path", anchor="center")
        self.tree.heading("Renamed", text="📝 Renamed As", anchor="center")
        self.tree.heading("Category", text="Category", anchor="center")
        self.tree.heading("Tags", text="Tags", anchor="center")

        self.tree.column("ID", width=60, anchor="center", minwidth=50)
        self.tree.column("Amount", width=120, anchor="e", minwidth=100)
        self.tree.column("Date", width=130, anchor="center", minwidth=120)
        self.tree.column("Original Path", width=300, anchor="w", minwidth=200)
        self.tree.column("Renamed", width=250, anchor="w", minwidth=200)
        self.tree.column("Category", width=120, anchor="center", minwidth=100)
        self.tree.column("Tags", width=150, anchor="w", minwidth=100)
        
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)
        self.tree.bind("<Double-1>", self.on_double_click)
        self.tree.bind("<Button-3>", self.show_context_menu)

    def create_enhanced_preview_panel(self):
        self.preview_panel.grid_rowconfigure(1, weight=1)
        self.preview_panel.grid_columnconfigure(0, weight=1)
        
        # Enhanced header
        header_frame = ctk.CTkFrame(self.preview_panel, height=60, corner_radius=0,
                                  fg_color=("#2e7d32", "#1b5e20"))
        header_frame.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        header_frame.grid_propagate(False)
        header_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(
            header_frame,
            text="🖼️ Document Preview",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="white"
        ).pack(pady=20)
        
        # Preview content area
        preview_content = ctk.CTkFrame(self.preview_panel, corner_radius=0)
        preview_content.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)
        preview_content.grid_columnconfigure(0, weight=1)
        preview_content.grid_rowconfigure(0, weight=1)
        
        # Preview area with border
        preview_area = ctk.CTkFrame(preview_content, corner_radius=10, border_width=2,
                                  border_color=("gray70", "gray30"))
        preview_area.pack(expand=True, fill="both", padx=20, pady=20)
        
        self.preview_label = ctk.CTkLabel(
            preview_area,
            text="📋 Select a record to view document preview\n\nSupported formats:\n• Images (JPG, PNG, BMP, etc.)\n• PDF Documents",
            font=ctk.CTkFont(size=12),
            text_color=("gray50", "gray60"),
            justify="center"
        )
        self.preview_label.pack(expand=True, fill="both", padx=10, pady=10)

    def create_enhanced_log_panel(self):
        self.log_panel.grid_columnconfigure(0, weight=1)
        self.log_panel.grid_rowconfigure(1, weight=1)

        # Enhanced log header with toggle functionality
        log_header = ctk.CTkFrame(self.log_panel, height=50, corner_radius=0,
                                fg_color=("#424242", "#303030"))
        log_header.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        log_header.grid_propagate(False)
        log_header.grid_columnconfigure(0, weight=1)
        
        header_content = ctk.CTkFrame(log_header, fg_color="transparent")
        header_content.pack(expand=True, fill="both", padx=20)
        
        ctk.CTkLabel(
            header_content,
            text="📋 Application Activity Log",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="white"
        ).pack(side="left", pady=12)
        
        # Log controls with minimize/maximize
        log_controls = ctk.CTkFrame(header_content, fg_color="transparent")
        log_controls.pack(side="right", pady=8)
        
        # Add minimize/maximize button
        self.toggle_log_btn = ctk.CTkButton(
            log_controls,
            text="🔽 Minimize",
            command=self.toggle_log_panel,
            width=100,
            height=30,
            font=ctk.CTkFont(size=10, weight="bold"),
            fg_color=("gray60", "gray40"),
            hover_color=("gray70", "gray50")
        )
        self.toggle_log_btn.pack(side="right", padx=(0, 10))
        
        clear_log_btn = ctk.CTkButton(
            log_controls,
            text="🗑️ Clear",
            command=self.clear_log,
            width=80,
            height=30,
            font=ctk.CTkFont(size=10, weight="bold"),
            fg_color=("gray60", "gray40"),
            hover_color=("gray70", "gray50")
        )
        clear_log_btn.pack(side="right", padx=(10, 0))

        # Enhanced log text area
        self.log_container = ctk.CTkFrame(self.log_panel, corner_radius=0)
        self.log_container.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)
        self.log_container.grid_columnconfigure(0, weight=1)
        self.log_container.grid_rowconfigure(0, weight=1)
        
        self.log_text = ctk.CTkTextbox(
            self.log_container,
            wrap=tk.WORD,
            font=ctk.CTkFont(family="Consolas", size=10),
            corner_radius=0
        )
        self.log_text.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)

    def toggle_log_panel(self):
        """Toggle log panel visibility to make action buttons accessible."""
        if self.log_minimized:
            # Show log panel
            self.log_container.grid()
            self.root.grid_rowconfigure(1, weight=1)
            self.toggle_log_btn.configure(text="🔽 Minimize")
            self.log_minimized = False
        else:
            # Hide log panel content, keep header
            self.log_container.grid_remove()
            self.root.grid_rowconfigure(1, weight=0, minsize=50)
            self.toggle_log_btn.configure(text="🔼 Maximize")
            self.log_minimized = True

    def clear_log(self):
        """Clear the log text area."""
        self.log_text.delete("1.0", tk.END)
        self.logger.info("Log cleared by user")

    def open_settings_window(self):
        if hasattr(self, 'settings_win') and self.settings_win.winfo_exists():
            self.settings_win.focus()
        else:
            self.settings_win = SettingsWindow(self)

    def update_stats(self):
        """Update the statistics panel with current data."""
        try:
            db_path = self.db_path_var.get() if hasattr(self, 'db_path_var') else self.db_path
            if not os.path.exists(db_path):
                self.total_records_label.configure(text="Total Records: 0")
                self.total_amount_label.configure(text="Total Amount: ₹0.00")
                self.date_range_label.configure(text="Date Range: N/A")
                return
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                # Total records
                cursor.execute("SELECT COUNT(*) FROM ImageData")
                total_records = cursor.fetchone()[0] or 0
                self.total_records_label.configure(text=f"Total Records: {total_records:,}")
                # Total amount
                cursor.execute("SELECT SUM(CAST(amount AS FLOAT)) FROM ImageData")
                total_amount = cursor.fetchone()[0] or 0.0
                self.total_amount_label.configure(text=f"Total Amount: ₹{total_amount:,.2f}")
                # Date range
                cursor.execute("SELECT MIN(date), MAX(date) FROM ImageData")
                min_date, max_date = cursor.fetchone()
                if min_date and max_date:
                    self.date_range_label.configure(text=f"Date Range: {min_date} to {max_date}")
                else:
                    self.date_range_label.configure(text="Date Range: N/A")
        except Exception as e:
            self.logger.error(f"Error updating statistics: {e}")
            self.total_records_label.configure(text="Total Records: 0")
            self.total_amount_label.configure(text="Total Amount: ₹0.00")
            self.date_range_label.configure(text="Date Range: N/A")

    def on_tree_select(self, event):
        """Handle row selection to show image preview."""
        selected_item = self.tree.focus()
        if not selected_item:
            return

        item_data = self.tree.item(selected_item, "values")
        file_path = item_data[3]  # Original Path

        if not os.path.exists(file_path):
            self.preview_label.configure(
                image=None, 
                text="❌ File Not Found\n\nThe selected file could not be located at the specified path."
            )
            return

        try:
            # Get file extension
            _, ext = os.path.splitext(file_path)
            
            if ext.lower() == '.pdf':
                # Convert first page of PDF to image
                try:
                    pages = convert_from_path(file_path, first_page=1, last_page=1)
                    if pages:
                        img = pages[0]
                    else:
                        raise Exception("No pages found in PDF")
                except Exception as e:
                    self.logger.error(f"Error converting PDF: {e}")
                    self.preview_label.configure(
                        image=None, 
                        text=f"⚠️ PDF Preview Error\n\n{e}"
                    )
                    return
            else:
                img = Image.open(file_path)

            # Get preview panel dimensions
            panel_width = self.preview_panel.winfo_width()
            panel_height = self.preview_panel.winfo_height()

            if panel_width < 100 or panel_height < 100:
                self.root.after(100, lambda: self.on_tree_select(event))
                return

            # Calculate aspect ratio and resize
            img_width, img_height = img.size
            aspect_ratio = img_width / img_height

            max_width = panel_width - 80
            max_height = panel_height - 140

            if img_width > img_height:
                new_width = min(max_width, img_width)
                new_height = int(new_width / aspect_ratio)
                if new_height > max_height:
                    new_height = max_height
                    new_width = int(new_height * aspect_ratio)
            else:
                new_height = min(max_height, img_height)
                new_width = int(new_height * aspect_ratio)
                if new_width > max_width:
                    new_width = max_width
                    new_height = int(new_width / aspect_ratio)

            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            photo = ImageTk.PhotoImage(img)
            self.preview_label.configure(image=photo, text="")
            self.preview_label.image = photo
            
        except Exception as e:
            self.preview_label.configure(
                image=None, 
                text=f"⚠️ Preview Error\n\nUnable to load preview:\n{str(e)}"
            )
            self.logger.error(f"Could not load preview for {file_path}: {e}")

    def setup_logger(self):
        """Set up the logger with queue handler."""
        self.logger = logging.getLogger('ExpenseTracker')
        self.logger.setLevel(logging.INFO)
        
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        queue_handler = QueueHandler(self.log_queue)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s',
                                   datefmt='%Y-%m-%d %H:%M:%S')
        queue_handler.setFormatter(formatter)
        self.logger.addHandler(queue_handler)
        
        log_dir = os.path.join("outputs", "logs")
        os.makedirs(log_dir, exist_ok=True)
        file_handler = logging.FileHandler(os.path.join(log_dir, "app.log"))
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        
        self.logger.info("Enhanced UI initialized successfully")

    def configure_treeview_style(self):
        """Configure enhanced treeview styling."""
        style = ttk.Style()
        style.theme_use("default")
        
        # Configure treeview colors and fonts
        style.configure(
            "Treeview",
            background="#2a2d2e",
            foreground="white",
            rowheight=30,
            fieldbackground="#2a2d2e",
            font=('Segoe UI', 10)
        )
        
        style.configure(
            "Treeview.Heading",
            background="#1f538d",
            foreground="white",
            font=('Segoe UI', 11, 'bold'),
            relief="flat"
        )
        
        style.map(
            'Treeview',
            background=[('selected', '#1f538d')],
            foreground=[('selected', 'white')]
        )
        
        # Enhanced row styling
        self.tree.tag_configure('oddrow', background='#383838')
        self.tree.tag_configure('evenrow', background='#2a2d2e')

    def browse_source(self):
        path = filedialog.askdirectory()
        if path: self.source_path_var.set(path)

    def browse_db(self):
        path = filedialog.asksaveasfilename(defaultextension=".db")
        if path: self.db_path_var.set(path)

    def start_analysis(self):
        source_path = self.source_path_var.get()
        db_path = self.db_path_var.get()

        if not os.path.isdir(source_path):
            messagebox.showerror("Error", "Please select a valid source directory.")
            return

        self.start_button.configure(state="disabled", text="🔄 Analyzing...")
        self.progress_bar.set(0)

        threading.Thread(target=self.process_images, args=(source_path, db_path), daemon=True).start()

    def stop_analysis(self):
        self.stop_requested = True
        self.start_button.configure(state="normal")
        logger.info("Image analysis has been stopped.")


    def process_images(self, source_path, db_path):
        """Process all images in the source path and update the UI."""
        try:
            self.logger.info(f"Starting analysis of folder: {source_path}")
            
            for processed_count, total_files in get_image_data(source_path, db_path):
                if total_files > 0:
                    progress = processed_count / total_files
                    self.root.after(0, self.progress_bar.set, progress)

            self.logger.info("Analysis complete.")

            self.stop_analysis()
            
            self.root.after(0, self.start_button.configure, {"state": "normal", "text": "▶️ Start Analysis"})
            

        except Exception as e:
            self.logger.error(f"A critical error occurred during analysis: {e}")
        finally:
            self.root.after(0, self.load_data_from_db, db_path)
            self.root.after(0, self.start_button.configure, {"state": "normal", "text": "▶️ Start Analysis"})

    def load_data_from_db(self, db_path):
        try:
            for item in self.tree.get_children():
                self.tree.delete(item)
            if not os.path.exists(db_path):
                self.update_stats()
                return
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, amount, date, original_path, rename_name, category, tags FROM ImageData ORDER BY id")
                rows = cursor.fetchall()
                self.logger.info(f"Loaded {len(rows)} records from database")
                for i, row in enumerate(rows):
                    tag = 'evenrow' if i % 2 == 0 else 'oddrow'
                    self.tree.insert("", "end", values=row, tags=(tag,))
            self.update_stats()
        except Exception as e:
            self.logger.error(f"Failed to load data from DB: {e}")
            self.update_stats()
            
    def consume_logs(self):
        try:
            while True:
                log = self.log_queue.get_nowait()
                self.log_text.insert(tk.END, log + "\n")
                self.log_text.see(tk.END)
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self.consume_logs)

    def export_to_csv(self):
        """Export the data from the database to a CSV file."""
        db_path = self.db_path_var.get()
        if not os.path.exists(db_path):
            messagebox.showerror("Error", "Database not found. Please run an analysis first.")
            return

        save_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )

        if not save_path:
            return

        try:
            with sqlite3.connect(db_path) as conn:
                df = pd.read_sql_query("SELECT id, amount, date, original_path, rename_name FROM ImageData", conn)
            
            df.to_csv(save_path, index=False)
            self.logger.info(f"Data successfully exported to {save_path}")
            messagebox.showinfo("Success", f"Data exported to {save_path}")
        except Exception as e:
            self.logger.error(f"Failed to export data to CSV: {e}")
            messagebox.showerror("Export Failed", f"An error occurred while exporting:\n{e}")

    def export_files(self):
        """Export analyzed files with their new names to a dated output folder."""
        db_path = self.db_path_var.get()
        if not os.path.exists(db_path):
            messagebox.showerror("Error", "No database found. Please run analysis first.")
            return

        current_date = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_dir = os.path.join("outputs", f"export_files_{current_date}")
        os.makedirs(export_dir, exist_ok=True)

        try:
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT original_path, rename_name FROM ImageData ORDER BY date ASC")
                files = cursor.fetchall()

                if not files:
                    messagebox.showinfo("Info", "No files found in database to export.")
                    return

                success_count = 0
                failed_files = []

                for index, (original_path, rename_name) in enumerate(files, start=1):
                    try:
                        if os.path.exists(original_path):
                            _, ext = os.path.splitext(original_path)
                            new_filename = f"{str(index).zfill(2)}_{rename_name}{ext}"
                            new_path = os.path.join(export_dir, new_filename)
                            
                            shutil.copy2(original_path, new_path)
                            success_count += 1
                            self.logger.info(f"Exported: {new_filename}")
                        else:
                            failed_files.append(original_path)
                            self.logger.warning(f"File not found: {original_path}")
                    except Exception as e:
                        failed_files.append(original_path)
                        self.logger.error(f"Error exporting {original_path}: {str(e)}")

                message = f"Successfully exported {success_count} files to:\n{export_dir}"
                if failed_files:
                    message += f"\n\nFailed to export {len(failed_files)} files."
                    self.logger.warning(f"Failed to export {len(failed_files)} files")
                
                messagebox.showinfo("Export Complete", message)
                
                if success_count > 0:
                    if sys.platform == "win32":
                        os.startfile(export_dir)
                    elif sys.platform == "darwin":
                        subprocess.run(["open", export_dir])
                    else:
                        subprocess.run(["xdg-open", export_dir])

        except Exception as e:
            self.logger.error(f"Error during file export: {str(e)}")
            messagebox.showerror("Export Error", f"An error occurred during export:\n{str(e)}")

    def delete_selected(self):
        """Delete selected record(s) from the database and update the display."""
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showwarning("Warning", "Please select record(s) to delete.")
            return

        count = len(selected_items)
        if not messagebox.askyesno("Confirm Delete", 
                                 f"Are you sure you want to delete {count} selected record{'s' if count > 1 else ''}?"):
            return

        db_path = self.db_path_var.get()
        deleted_count = 0

        try:
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                for item in selected_items:
                    try:
                        record_id = self.tree.item(item)['values'][0]
                        cursor.execute("DELETE FROM ImageData WHERE id = ?", (record_id,))
                        self.tree.delete(item)
                        deleted_count += 1
                        self.logger.info(f"Deleted record ID: {record_id}")
                    except Exception as e:
                        self.logger.error(f"Error deleting record {record_id}: {str(e)}")

            conn.commit()
            messagebox.showinfo("Success", f"Successfully deleted {deleted_count} record{'s' if deleted_count > 1 else ''}.")
            self.load_data_from_db(db_path)
            self.update_stats()

        except Exception as e:
            self.logger.error(f"Error during deletion: {str(e)}")
            messagebox.showerror("Delete Error", f"An error occurred during deletion:\n{str(e)}")
            self.update_stats()

    def on_double_click(self, event):
        """Handle double-click to edit a cell."""
        region = self.tree.identify_region(event.x, event.y)
        if region != "cell":
            return

        selected_item = self.tree.focus()
        column = self.tree.identify_column(event.x)
        column_index = int(column.replace('#', '')) - 1

        if not selected_item or column_index < 1:
            return

        item_values = self.tree.item(selected_item, "values")
        old_value = item_values[column_index]
        
        new_value = simpledialog.askstring(
            "Edit Cell", f"Enter new value for {self.tree.heading(column)['text']}:",
            initialvalue=old_value
        )

        if new_value is not None and new_value != old_value:
            self.update_record_in_db(selected_item, column_index, new_value)

    def update_record_in_db(self, item_id, col_index, new_value):
        """Update a specific field for a record in the database."""
        db_path = self.db_path_var.get()
        item_values = list(self.tree.item(item_id, "values"))
        record_id = item_values[0]

        column_names = ["id", "amount", "date", "original_path", "rename_name"]
        column_to_update = column_names[col_index]

        try:
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                query = f"UPDATE ImageData SET {column_to_update} = ? WHERE id = ?"
                cursor.execute(query, (new_value, record_id))
                conn.commit()
            
            item_values[col_index] = new_value
            self.tree.item(item_id, values=item_values)
            self.logger.info(f"Record {record_id} updated. Set {column_to_update} to {new_value}.")
        except Exception as e:
            self.logger.error(f"Failed to update record {record_id}: {e}")
            messagebox.showerror("Update Failed", f"Could not update the database:\n{e}")

    def show_context_menu(self, event):
        """Show a right-click context menu on a treeview item."""
        selected_item = self.tree.identify_row(event.y)
        if not selected_item:
            return

        self.tree.selection_set(selected_item)
        item_data = self.tree.item(selected_item, "values")
        file_path = item_data[3]

        context_menu = tk.Menu(self.root, tearoff=0)
        context_menu.add_command(label="Show in Folder", command=lambda: self.show_in_folder(file_path))
        
        context_menu.tk_popup(event.x_root, event.y_root)

    def show_in_folder(self, path):
        """Open the file explorer to the location of the given file."""
        if not os.path.exists(path):
            self.logger.error(f"Cannot show in folder: File not found at {path}")
            messagebox.showerror("File Not Found", f"The file could not be found at:\n{path}")
            return
        
        if sys.platform == "win32":
            os.startfile(os.path.dirname(path))
        elif sys.platform == "darwin":
            subprocess.run(["open", "-R", path])
        else:
            subprocess.run(["xdg-open", os.path.dirname(path)])

    def update_paths_in_ui(self):
        """Update the display when paths change in settings."""
        self.logger.info(f"Paths updated. Source: {self.source_path}, DB: {self.db_path}")

def run_ui():
    root = ctk.CTk()
    app = ImageAnalyzerUI(root)
    root.mainloop()

if __name__ == "__main__":
    run_ui()
