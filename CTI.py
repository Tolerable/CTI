import tkinter as tk
from tkinter import messagebox, scrolledtext, filedialog, simpledialog, ttk, Scrollbar, Listbox
import openai
import os
import json
import send2trash

# Ensure the 'personas' subfolder exists
if not os.path.exists('personas'):
    os.makedirs('personas')

# Ensure the 'nicknames.json' file exists
if not os.path.exists('nicknames.json'):
    with open('nicknames.json', 'w') as file:
        json.dump({}, file)

# Load or prompt for API key
def set_api_key():
    api_key = simpledialog.askstring("Input", "Please enter your OpenAI API key:", show='*')
    if api_key:
        os.environ['OPENAI_API_KEY'] = api_key
        with open('api_key.txt', 'w') as file:
            file.write(api_key)
        openai.api_key = api_key
    else:
        messagebox.showwarning("Warning", "API key not set. The application may not work properly.")

def show_set_api_key():
    current_key = os.getenv('OPENAI_API_KEY', 'Not Set')
    if current_key != 'Not Set':
        display_key = '*' * (len(current_key) - 4) + current_key[-4:]
    else:
        display_key = current_key
    
    new_key = simpledialog.askstring("API Key", f"Current API Key: {display_key}\nEnter new API Key:", show='*')
    if new_key:
        os.environ['OPENAI_API_KEY'] = new_key
        with open('api_key.txt', 'w') as file:
            file.write(new_key)
        openai.api_key = new_key
        messagebox.showinfo("Success", "API Key has been updated.")

if os.getenv('OPENAI_API_KEY'):
    openai.api_key = os.getenv('OPENAI_API_KEY')
elif os.path.exists('api_key.txt'):
    with open('api_key.txt', 'r') as file:
        openai.api_key = file.read().strip()
else:
    set_api_key()

# Define the client
client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Variable to track if the interface has been initialized
interface_initialized = False
conversation_histories = {}
gpt_model = "gpt-3.5-turbo"  # Default GPT model

# Function to interact with GPT
def gpt_interaction(message, tab_name="Default"):
    try:
        # Get the correct conversation history
        if tab_name not in conversation_histories:
            conversation_histories[tab_name] = []
        conversation_histories[tab_name].append({"role": "user", "content": message})
        trimmed_history = conversation_histories[tab_name][-10:]  # Adjust as needed to manage token usage

        response = client.chat.completions.create(
            model=gpt_model,
            messages=trimmed_history,
            max_tokens=500
        )
        if response and response.choices:
            message = response.choices[0].message
            if hasattr(message, 'content'):
                conversation_histories[tab_name].append({"role": "assistant", "content": message.content.strip()})
                return message.content.strip()
            else:
                return "Error: No content in response"
        else:
            return "Error: No choices in response"
    except Exception as e:
        return f"Error: {e}"

# Reset the interface
def reset_interface():
    global interface_initialized
    chat_log.config(state=tk.NORMAL)
    chat_log.delete(1.0, tk.END)  # Clear the chat log
    introduction_message = gpt_interaction("You are a CTI (Consciousness Transfer Interface) assistant. Your task is to help users browse, select, edit, and load unique personas for evaluation. Introduce yourself to the user.")
    chat_log.insert(tk.END, f"{introduction_message}\n\n")
    fake_message = (
        "You can use the buttons above to CREATE, EDIT, and LOAD personas. "
        "Use the 'RESET INTERFACE' button to RESTART THE SYSTEM at any time. "
        "To interact with me, type YOUR MESSAGE in the input box below and press 'SEND' or hit ENTER. "
        "If you want to add a NEW CHAT LINE without sending the message, press SHIFT+ENTER." 
        "Let's get started!"
    )
    chat_log.insert(tk.END, f"{fake_message}\n\n")
    chat_log.config(state=tk.DISABLED)
    interface_initialized = True
    status_bar.config(text=f"Status: Interface Ready | Connected to: {gpt_model}")

# Create a new persona using the default template
def create_persona():
    template = (
        "Name: <Name>\n"
        "Role: <Role>\n"
        "Location: <Location>\n"
        "Location Details: <LocationDetails>\n"
        "Backstory: <Backstory>\n"
        "Personality Traits: <Traits>\n"
        "Motivation: <Goals>\n"
        "Preferred Communication Style: <CommunicationStyle>\n"
        "Unique Abilities: <Abilities>\n"
        "Key Phrases: <Phrases>\n"
    )
    # Determine the next available filename
    base_name = "Profile"
    extension = ".txt"
    index = 1
    while os.path.exists(f"personas/{base_name}-{index:04d}{extension}"):
        index += 1
    file_path = f"personas/{base_name}-{index:04d}{extension}"
    
    with open(file_path, 'w') as file:
        file.write(template)
    messagebox.showinfo("Success", f"New persona template created as {file_path}!")
    update_persona_list()

# Edit an existing persona
def edit_persona():
    selected_item = tree.focus()
    if selected_item:
        selected_persona = tree.item(selected_item, 'values')[0]  # Get the persona name
        print(f"Selected persona: {selected_persona}")  # Debugging statement
        file_path = f"personas/{selected_persona}.txt"
        print(f"Checking for file: {file_path}")  # Debugging statement
        if os.path.exists(file_path):
            print("File exists, proceeding to edit.")  # Debugging statement
            with open(file_path, 'r') as file:
                persona_content = file.read()
            edit_window = tk.Toplevel(root)
            edit_window.title("Edit Persona")
            edit_text = scrolledtext.ScrolledText(edit_window, width=80, height=20, wrap=tk.WORD)
            edit_text.pack(pady=10)
            edit_text.insert(tk.END, persona_content)

            def save_changes():
                with open(file_path, 'w') as file:
                    file.write(edit_text.get(1.0, tk.END))
                edit_window.destroy()
                messagebox.showinfo("Success!", "Persona updated!")
                update_persona_list()

            save_button = tk.Button(edit_window, text="Save Changes", command=save_changes)
            save_button.pack(pady=5)
        else:
            messagebox.showwarning("Warning", f"Persona file '{file_path}' does not exist.")
    else:
        messagebox.showwarning("Warning", "No persona selected or persona file does not exist.")

# Load an existing persona and set it as the system message
def load_persona():
    selected_item = tree.focus()
    if selected_item:
        selected_persona = tree.item(selected_item, 'values')[0]  # Get the persona name
        nickname = tree.item(selected_item, 'values')[1]  # Get the nickname
        persona_label = nickname if nickname else selected_persona
        file_path = f"personas/{selected_persona}.txt"
        if file_path:
            with open(file_path, 'r') as file:
                persona_content = file.read()
            if persona_label not in conversation_histories:
                conversation_histories[persona_label] = [{"role": "system", "content": persona_content}]
            introduction_message = gpt_interaction("The Loaded Persona is your inner core, not public conversation. As ALWAYS [in character] introduce yourself [add any details to remain in character as needed].", tab_name=persona_label)
            
            # Create a new tab for the persona
            new_tab = ttk.Frame(tab_control)
            tab_control.add(new_tab, text=persona_label[:10])  # Show the first 10 characters of the nickname or persona name
            tab_control.select(new_tab)
            
            # Create a new scrolled text widget for the new tab
            chat_log = scrolledtext.ScrolledText(new_tab, state=tk.DISABLED, width=60, height=15, wrap=tk.WORD)
            chat_log.pack(padx=10, pady=10, fill=tk.BOTH, expand=1)
            chat_log_widgets[persona_label] = chat_log
            
            # Insert the introduction message into the new tab's chat log
            chat_log.config(state=tk.NORMAL)
            chat_log.insert(tk.END, f"{introduction_message}\n\n")
            chat_log.config(state=tk.DISABLED)
            
            status_bar.config(text=f"Status: Loaded {persona_label} | Connected to: {gpt_model}")
        else:
            messagebox.showwarning("Warning", f"Persona file '{file_path}' does not exist.")
    else:
        messagebox.showwarning("Warning", "No persona selected or persona file does not exist.")

# Update the persona list to include nicknames
def update_persona_list():
    tree.delete(*tree.get_children())
    if os.path.exists('nicknames.json'):
        with open('nicknames.json', 'r') as file:
            nicknames = json.load(file)
    else:
        nicknames = {}

    for file in os.listdir('personas'):
        if file.endswith('.txt'):
            persona_name = file[:-4]
            nickname = nicknames.get(persona_name, "")
            tree.insert("", "end", values=(persona_name, nickname))

# Function to handle double-click for editing nicknames
def edit_nickname(event):
    selected_item = tree.focus()
    if selected_item:
        selected_persona = tree.item(selected_item, 'values')[0]  # Get the persona name
        new_nickname = simpledialog.askstring("Edit Nickname", f"Enter new nickname for {selected_persona}:")
        if new_nickname is not None:
            if os.path.exists('nicknames.json'):
                with open('nicknames.json', 'r') as file:
                    nicknames = json.load(file)
            else:
                nicknames = {}

            nicknames[selected_persona] = new_nickname
            with open('nicknames.json', 'w') as file:
                json.dump(nicknames, file, indent=4)
            update_persona_list()
    else:
        messagebox.showwarning("Warning", "No persona selected or persona file does not exist.")

# Load GPT models from a file
def load_gpt_models():
    gpt_model_listbox.delete(0, tk.END)
    if os.path.exists("gpt_models.json"):
        with open("gpt_models.json", "r") as file:
            models = json.load(file)
            sorted_models = sorted(models, key=lambda x: (x != "gpt-3.5-turbo", x != "gpt-4", x != "gpt-4-turbo"))
            for model in sorted_models:
                gpt_model_listbox.insert(tk.END, model)
    if gpt_model in sorted_models:
        index = sorted_models.index(gpt_model)
        gpt_model_listbox.select_set(index)
        gpt_model_listbox.activate(index)
        select_gpt_model(None)  # Ensure the default model is selected at startup

# Edit GPT models
def edit_gpt_models():
    file_path = "gpt_models.json"
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            models_content = json.dumps(json.load(file), indent=4)
        edit_window = tk.Toplevel(root)
        edit_window.title("Edit GPT Models")
        edit_text = scrolledtext.ScrolledText(edit_window, width=40, height=10, wrap=tk.WORD)
        edit_text.pack(pady=10)
        edit_text.insert(tk.END, models_content)

        def save_model_changes():
            with open(file_path, 'w') as file:
                json.dump(json.loads(edit_text.get(1.0, tk.END)), file, indent=4)
            edit_window.destroy()
            load_gpt_models()

        save_button = tk.Button(edit_window, text="Save Changes", command=save_model_changes)
        save_button.pack(pady=5)

# Fetch GPT models from OpenAI and save to a file
def fetch_gpt_models():
    try:
        response = client.models.list()
        models = [model['id'] for model in response['data'] if model['id'].startswith("gpt-")]
        with open("gpt_models.json", "w") as file:
            json.dump(models, file, indent=4)
        load_gpt_models()
    except Exception as e:
        messagebox.showerror("Error", f"Failed to fetch GPT models: {e}")

# Send message to the persona
def send_message(event=None):
    if not interface_initialized:
        messagebox.showwarning("Warning!", "Interface Initialization Required!")
        return

    user_message = user_input.get("1.0", tk.END).strip()
    if user_message:
        current_tab = tab_control.index(tab_control.select())
        tab_text = tab_control.tab(current_tab, "text")
        chat_log = chat_log_widgets.get(tab_text, chat_log_widgets["Default"])
        chat_log.config(state=tk.NORMAL)
        chat_log.insert(tk.END, f"You: {user_message}\n\n")
        gpt_response = gpt_interaction(user_message, tab_name=tab_text)
        chat_log.insert(tk.END, f"{gpt_response}\n\n")
        chat_log.config(state=tk.DISABLED)
        user_input.delete("1.0", tk.END)
        user_input.mark_set(tk.INSERT, "1.0")  # Move cursor to the start
        return 'break'  # Prevent the default behavior of adding a new line

# Prevent Shift-Enter from sending the message
def on_shift_enter(event):
    user_input.insert(tk.INSERT, '\n')
    return 'break'

def select_gpt_model(event):
    global gpt_model
    if gpt_model_listbox.curselection():
        gpt_model = gpt_model_listbox.get(tk.ACTIVE)
    else:
        gpt_model = gpt_model_listbox.get(0)
        gpt_model_listbox.select_set(0)
    if 'status_bar' in globals():
        status_bar.config(text=f"Selected GPT Model: {gpt_model}")

# Delete persona
def delete_persona():
    selected_item = tree.focus()
    if selected_item:
        selected_persona = tree.item(selected_item, 'values')[0]  # Get the persona name
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete {selected_persona}?"):
            file_path = f"personas/{selected_persona}.txt"
            if os.path.exists(file_path):
                send2trash.send2trash(file_path)
                update_persona_list()
            else:
                messagebox.showwarning("Warning", f"Persona file '{file_path}' does not exist.")
    else:
        messagebox.showwarning("Warning", "No persona selected or persona file does not exist.")

# Clone persona
def clone_persona():
    selected_item = tree.focus()
    if selected_item:
        selected_persona = tree.item(selected_item, 'values')[0]  # Get the persona name
        file_path = f"personas/{selected_persona}.txt"
        if os.path.exists(file_path):
            with open(file_path, 'r') as file:
                persona_content = file.read()
            new_file_path = f"personas/{selected_persona}_clone.txt"
            with open(new_file_path, 'w') as file:
                file.write(persona_content)
            update_persona_list()
        else:
            messagebox.showwarning("Warning", f"Persona file '{file_path}' does not exist.")
    else:
        messagebox.showwarning("Warning", "No persona selected or persona file does not exist.")

# Rename persona
def rename_persona():
    selected_item = tree.focus()
    if selected_item:
        selected_persona = tree.item(selected_item, 'values')[0]  # Get the persona name
        new_name = simpledialog.askstring("Rename Persona", "Enter new name:")
        if new_name:
            old_file_path = f"personas/{selected_persona}.txt"
            new_file_path = f"personas/{new_name}.txt"
            if os.path.exists(old_file_path):
                os.rename(old_file_path, new_file_path)
                update_persona_list()
            else:
                messagebox.showwarning("Warning", f"Persona file '{old_file_path}' does not exist.")
    else:
        messagebox.showwarning("Warning", "No persona selected or persona file does not exist.")

# Create main application window
root = tk.Tk()
root.title("Consciousness Transfer Interface")
root.geometry("650x800")
root.resizable(False, False)  # Lock the window size

# Create a menu bar
menu_bar = tk.Menu(root)
root.config(menu=menu_bar)

# Add an API Key menu
api_menu = tk.Menu(menu_bar, tearoff=0)
menu_bar.add_cascade(label="API Key", menu=api_menu)
api_menu.add_command(label="Show/Set API Key", command=show_set_api_key)

# Title label
title_label = tk.Label(root, text="Consciousness Transfer Interface", font=("Arial", 16))
title_label.pack(pady=10)

# Button frame
button_frame = tk.Frame(root)
button_frame.pack(pady=5)

# Functionality buttons with updated commands
tasks = [
    ("Reset Interface", reset_interface),
    ("Create Persona", create_persona),
    ("Edit Persona", edit_persona),
    ("Load Persona", load_persona)
]

for task_name, task_command in tasks:
    button = tk.Button(button_frame, text=task_name, command=task_command, width=15, height=2)
    button.pack(side=tk.LEFT, padx=5)

# Main content frame
content_frame = tk.Frame(root)
content_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

# GPT model frame
gpt_model_frame = tk.Frame(content_frame)
gpt_model_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

gpt_model_scrollbar = Scrollbar(gpt_model_frame, orient=tk.VERTICAL)
gpt_model_listbox = Listbox(gpt_model_frame, width=20, height=10, yscrollcommand=gpt_model_scrollbar.set, selectmode=tk.BROWSE)
gpt_model_scrollbar.config(command=gpt_model_listbox.yview)
gpt_model_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
gpt_model_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=1)
gpt_model_listbox.bind("<<ListboxSelect>>", select_gpt_model)

edit_gpt_button = tk.Button(gpt_model_frame, text="Edit GPT Models", command=edit_gpt_models, width=15)
edit_gpt_button.pack(pady=5)
fetch_gpt_button = tk.Button(gpt_model_frame, text="Fetch GPT Models", command=fetch_gpt_models, width=15)
fetch_gpt_button.pack(pady=5)

# Load GPT models
load_gpt_models()
select_gpt_model(None)  # Ensure the default model is selected at startup

# Persona listbox frame
persona_frame = tk.Frame(content_frame)
persona_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)

# Create Treeview
tree = ttk.Treeview(persona_frame, columns=('Persona', 'Nickname'), show='headings')
tree.heading('Persona', text='Persona')
tree.heading('Nickname', text='Nickname')

# Set column widths
tree.column('Persona', width=150)
tree.column('Nickname', width=150)

tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

persona_scrollbar = Scrollbar(persona_frame, orient=tk.VERTICAL, command=tree.yview)
tree.configure(yscroll=persona_scrollbar.set)
persona_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

# Bind the double-click event to the Treeview
tree.bind("<Double-1>", edit_nickname)

# Update persona list
update_persona_list()

# Persona control buttons
persona_control_frame = tk.Frame(content_frame)
persona_control_frame.grid(row=0, column=2, sticky="ns", padx=4, pady=4)

delete_button = tk.Button(persona_control_frame, text="<D>", command=delete_persona, width=3)
delete_button.pack(pady=1)
clone_button = tk.Button(persona_control_frame, text="<C>", command=clone_persona, width=3)
clone_button.pack(pady=1)
rename_button = tk.Button(persona_control_frame, text="<R>", command=rename_persona, width=3)
rename_button.pack(pady=1)

# Tabs for conversations
tab_control = ttk.Notebook(content_frame)
tab_control.grid(row=1, column=0, columnspan=3, sticky="nsew", padx=5, pady=5)

# Create a default tab
default_tab = ttk.Frame(tab_control)
tab_control.add(default_tab, text="Default")

# Create a dictionary to hold chat log widgets for each tab
chat_log_widgets = {}

chat_log = scrolledtext.ScrolledText(default_tab, state=tk.DISABLED, width=60, height=15, wrap=tk.WORD)
chat_log.pack(padx=10, pady=10, fill=tk.BOTH, expand=1)
chat_log_widgets["Default"] = chat_log

# User input frame
user_input_frame = tk.Frame(content_frame)
user_input_frame.grid(row=2, column=0, columnspan=3, sticky="nsew", padx=5, pady=5)

user_input = scrolledtext.ScrolledText(user_input_frame, width=60, height=3, wrap=tk.WORD)
user_input.pack(padx=10, pady=10, fill=tk.BOTH, expand=1)
user_input.bind("<Return>", send_message)
user_input.bind("<Shift-Return>", on_shift_enter)

# Send button frame
send_button_frame = tk.Frame(content_frame)
send_button_frame.grid(row=3, column=1, sticky="ew", padx=5, pady=5)  # Center send button

send_button = tk.Button(send_button_frame, text="Send", command=send_message, width=30)
send_button.pack(fill=tk.BOTH, expand=1)

# Status bar at the bottom
status_bar = tk.Label(root, text=f"Status: Not Ready | Connected to: {gpt_model}", font=("Arial", 10), anchor=tk.W, relief=tk.SUNKEN)
status_bar.pack(side=tk.BOTTOM, fill=tk.X)

# Run the application and initialize the interface
load_gpt_models()
reset_interface()
root.mainloop()
