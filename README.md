# 🛠️ Bashrc Alias Manager Toolkit

## 📌 Overview

**Bashrc Alias Manager Toolkit** is a modern, GUI-based Python application designed to simplify the management of bash aliases. The tool provides a user-friendly interface for creating, editing, organizing, and tracking your bash aliases, making terminal workflow optimization more accessible than ever.

## 🎯 Features

- ✅ **Intuitive Interface** - Easy-to-use graphical interface built with Tkinter
- ✅ **Full Alias Management** - Create, edit, delete, and organize aliases in sections
- ✅ **Search & Filter** - Quickly find aliases by name, command, or description
- ✅ **Section Organization** - Group aliases by function or category
- ✅ **Detailed Descriptions** - Add helpful descriptions to remember what each alias does
- ✅ **Import/Export** - Share alias configurations between systems
- ✅ **Backup System** - Create backups of your .bashrc before making changes
- ✅ **Undo/Redo** - Safely experiment with changes using full undo/redo functionality

## 🖥️ Screenshot

![Bashrc Alias Manager Toolkit](https://i.ibb.co/nqVsDPhT/13-03-2025-T17-29-28.png)

## 🛠️ Requirements

Before running the script, ensure you have the following installed:

- Python 3.x
- Tkinter (usually included with Python)

## 📥 Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/saymonn37/Bashrc-Alias-Manager-Toolkit.git
   cd Bashrc-Alias-Manager-Toolkit
   ```

2. Run the script:

   ```bash
   python3 alias_manager_toolkit.py
   ```

## 🚀 Usage

### Basic Operations

1. **View Aliases** - All your current bash aliases are displayed in the main table
2. **Create Alias** - Click "New" and fill in the details in the form
3. **Edit Alias** - Select an alias from the table and modify its properties
4. **Delete Alias** - Select an alias and click "Delete" or press the Delete key
5. **Search** - Type in the search box to filter aliases by name, command, or description
6. **Filter by Section** - Use the dropdown to view aliases from a specific section

### Section Management

1. **Add Section** - Create new organizational sections for your aliases
2. **Rename Section** - Change the name of an existing section
3. **Delete Section** - Remove empty sections (sections with aliases cannot be deleted)

### Backup and Import/Export

1. **Backup .bashrc** - Create timestamped backups of your .bashrc file
2. **Export Aliases** - Save your aliases to a JSON file for sharing or backup
3. **Import Aliases** - Load aliases from a previously exported JSON file

### Keyboard Shortcuts

- **Ctrl+N** - Create new alias
- **Ctrl+S** - Save current alias
- **Ctrl+Z** - Undo last action
- **Ctrl+Y** - Redo last undone action
- **Delete** - Delete selected alias
- **F5** - Refresh the application

## 🔍 GUI Overview

The application is divided into two main panels:

### Left Panel
- **Search and Filter** - Tools to quickly find specific aliases
- **Alias List** - Sortable table showing all aliases with their details

### Right Panel
- **Alias Details** - Form for viewing and editing alias properties
- **Action Buttons** - Controls for creating, saving, and deleting aliases
- **Section Management** - Tools for organizing aliases into sections
- **Backup and Import/Export** - Options for saving and sharing configurations

## 📋 Technical Details

- The application automatically detects and parses aliases from your .bashrc file
- Alias descriptions are stored in a separate JSON file for persistence
- The application creates automatic backups before making significant changes
- Settings like window size and column widths are saved between sessions

## 🛑 Troubleshooting

| Issue | Solution |
|-------|----------|
| Window size resets | Check if the application has write permissions to its directory |
| Aliases not appearing | Ensure your .bashrc follows the expected format with a "# CUSTOM ALIASES" section |
| Changes not taking effect | Remember to source your .bashrc file (`source ~/.bashrc`) after making changes |
| Import failing | Verify the JSON file was exported from a compatible version of this tool |

## 🔧 Future Improvements

- Support for additional shell configurations (zsh, fish)
- Cloud synchronization for sharing aliases between systems
- Advanced regex search for finding complex commands
- Alias suggestion based on command history analysis

## 📝 License

This project is open-source.

## 👤 Author

Developed by [Saymonn](https://github.com/saymonn37)
