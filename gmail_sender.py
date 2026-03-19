"""
Gmail Sender - Works with generated credentials
Simple GUI to send emails using the JSON credentials from bulk_gmail_auth.py
"""
import os
import json
import base64
import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


class GmailSenderGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Gmail Sender - Apex")
        self.root.geometry("800x700")
        self.root.minsize(700, 600)
        
        self.credentials = None
        self.current_email = None
        
        self.create_widgets()
        
    def create_widgets(self):
        # Title
        title = tk.Label(self.root, text="Gmail Sender", font=('Arial', 20, 'bold'), fg='#333')
        title.pack(pady=10)
        
        # Main Frame
        main = tk.Frame(self.root, padx=20, pady=10)
        main.pack(fill=tk.BOTH, expand=True)
        
        # Credentials Section
        cred_frame = tk.LabelFrame(main, text="Credentials", font=('Arial', 10, 'bold'), padx=10, pady=10)
        cred_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(cred_frame, text="Credentials JSON:", font=('Arial', 10)).grid(row=0, column=0, sticky=tk.W)
        self.cred_path = tk.Entry(cred_frame, font=('Arial', 10), width=50)
        self.cred_path.grid(row=0, column=1, padx=5, sticky=tk.EW)
        tk.Button(cred_frame, text="Browse", command=self.browse_cred, font=('Arial', 9)).grid(row=0, column=2)
        tk.Button(cred_frame, text="Load", command=self.load_credentials, font=('Arial', 9), bg='#4CAF50', fg='white').grid(row=0, column=3, padx=5)
        
        self.cred_status = tk.Label(cred_frame, text="No credentials loaded", font=('Arial', 9), fg='red')
        self.cred_status.grid(row=1, column=0, columnspan=4, sticky=tk.W, pady=5)
        
        cred_frame.columnconfigure(1, weight=1)
        
        # Quick Account Buttons
        self.quick_frame = tk.LabelFrame(main, text="Quick Select (from credentials folder)", font=('Arial', 10, 'bold'), padx=10, pady=5)
        self.quick_frame.pack(fill=tk.X, pady=5)
        self.refresh_quick_buttons()
        
        # Email Content
        email_frame = tk.LabelFrame(main, text="Email Content", font=('Arial', 10, 'bold'), padx=10, pady=10)
        email_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        tk.Label(email_frame, text="To:", font=('Arial', 10)).grid(row=0, column=0, sticky=tk.W)
        self.to_entry = tk.Entry(email_frame, font=('Arial', 10))
        self.to_entry.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=2)
        tk.Button(email_frame, text="Load List", command=self.load_email_list, font=('Arial', 9)).grid(row=0, column=2)
        
        tk.Label(email_frame, text="Subject:", font=('Arial', 10)).grid(row=1, column=0, sticky=tk.W)
        self.subject_entry = tk.Entry(email_frame, font=('Arial', 10))
        self.subject_entry.grid(row=1, column=1, sticky=tk.EW, padx=5, pady=2)
        
        tk.Label(email_frame, text="From Name:", font=('Arial', 10)).grid(row=2, column=0, sticky=tk.W)
        self.name_entry = tk.Entry(email_frame, font=('Arial', 10))
        self.name_entry.grid(row=2, column=1, sticky=tk.EW, padx=5, pady=2)
        
        email_frame.columnconfigure(1, weight=1)
        
        # Body
        tk.Label(email_frame, text="Message (HTML supported):", font=('Arial', 10)).grid(row=3, column=0, sticky=tk.W, pady=(10, 2))
        self.body_text = scrolledtext.ScrolledText(email_frame, height=12, font=('Consolas', 10), wrap=tk.WORD)
        self.body_text.grid(row=4, column=0, columnspan=3, sticky=tk.NSEW, pady=2)
        
        # HTML Toggle
        self.html_var = tk.BooleanVar(value=True)
        tk.Checkbutton(email_frame, text="Send as HTML", variable=self.html_var, font=('Arial', 9)).grid(row=5, column=0, sticky=tk.W, pady=5)
        
        email_frame.rowconfigure(4, weight=1)
        email_frame.columnconfigure(1, weight=1)
        
        # Buttons
        btn_frame = tk.Frame(main, pady=10)
        btn_frame.pack(fill=tk.X)
        
        self.send_btn = tk.Button(btn_frame, text="Send Email", command=self.send_email, font=('Arial', 12, 'bold'), 
                                  bg='#2196F3', fg='white', padx=30, pady=10, state=tk.DISABLED)
        self.send_btn.pack(side=tk.LEFT, padx=5)
        
        tk.Button(btn_frame, text="Clear", command=self.clear, font=('Arial', 10), padx=20, pady=8).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Test Connection", command=self.test_connection, font=('Arial', 10), padx=20, pady=8).pack(side=tk.RIGHT, padx=5)
        
        # Log
        log_frame = tk.LabelFrame(main, text="Log", font=('Arial', 10, 'bold'), padx=5, pady=5)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=6, font=('Consolas', 9), state=tk.DISABLED)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
    def refresh_quick_buttons(self):
        """Create quick select buttons for each credential file"""
        for widget in self.quick_frame.winfo_children():
            widget.destroy()
            
        cred_dir = Path("credentials")
        if not cred_dir.exists():
            tk.Label(self.quick_frame, text="No credentials folder found", font=('Arial', 9), fg='gray').pack()
            return
            
        cred_files = list(cred_dir.glob("*_credentials.json"))
        if not cred_files:
            tk.Label(self.quick_frame, text="No credential files found", font=('Arial', 9), fg='gray').pack()
            return
        
        for cred_file in sorted(cred_files):
            email = self.get_email_from_cred(cred_file)
            display = email or cred_file.stem.replace("_credentials", "")
            btn = tk.Button(self.quick_frame, text=display, font=('Arial', 9), 
                          command=lambda f=cred_file: self.select_cred(f))
            btn.pack(side=tk.LEFT, padx=2, pady=2)
            
    def get_email_from_cred(self, cred_file):
        try:
            with open(cred_file, 'r') as f:
                data = json.load(f)
                return data.get('account_email', '')
        except:
            return ''
            
    def select_cred(self, cred_file):
        self.cred_path.delete(0, tk.END)
        self.cred_path.insert(0, str(cred_file))
        self.load_credentials()
        
    def browse_cred(self):
        filename = filedialog.askopenfilename(
            title="Select Credentials JSON",
            filetypes=[("JSON files", "*.json")],
            initialdir="credentials"
        )
        if filename:
            self.cred_path.delete(0, tk.END)
            self.cred_path.insert(0, filename)
            
    def load_credentials(self):
        path = self.cred_path.get()
        if not path or not os.path.exists(path):
            messagebox.showerror("Error", "Credentials file not found!")
            return
            
        try:
            with open(path, 'r') as f:
                creds_info = json.load(f)
            
            self.credentials = Credentials(
                token=creds_info['token'],
                refresh_token=creds_info['refresh_token'],
                token_uri=creds_info['token_uri'],
                client_id=creds_info['client_id'],
                client_secret=creds_info['client_secret'],
                scopes=creds_info['scopes']
            )
            
            self.current_email = creds_info.get('account_email', 'Unknown')
            self.cred_status.config(text=f"✓ Loaded: {self.current_email}", fg='green')
            self.send_btn.config(state=tk.NORMAL)
            self.log(f"Credentials loaded for: {self.current_email}")
            
            # Auto-fill from name if empty
            if not self.name_entry.get() and self.current_email:
                default_name = self.current_email.split('@')[0].replace('.', ' ').title()
                self.name_entry.insert(0, default_name)
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load credentials:\n{e}")
            self.cred_status.config(text="Failed to load", fg='red')
            
    def load_email_list(self):
        filename = filedialog.askopenfilename(
            title="Select Email List (txt file)",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filename:
            try:
                with open(filename, 'r') as f:
                    emails = [line.strip() for line in f if line.strip() and '@' in line]
                self.to_entry.delete(0, tk.END)
                self.to_entry.insert(0, ', '.join(emails[:10]))  # Show first 10
                self.log(f"Loaded {len(emails)} emails from {filename}")
                if len(emails) > 10:
                    self.log(f"(Showing first 10, total: {len(emails)})")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load email list: {e}")
                
    def test_connection(self):
        if not self.credentials:
            messagebox.showerror("Error", "Load credentials first!")
            return
            
        try:
            service = build('gmail', 'v1', credentials=self.credentials)
            profile = service.users().getProfile(userId='me').execute()
            email = profile.get('emailAddress', 'Unknown')
            messages = service.users().messages().list(userId='me', maxResults=1).execute()
            count = messages.get('resultSizeEstimate', 0)
            
            self.log(f"✓ Connection successful!")
            self.log(f"  Account: {email}")
            self.log(f"  Messages: ~{count}")
            messagebox.showinfo("Success", f"Connection successful!\n\nAccount: {email}")
        except Exception as e:
            self.log(f"✗ Connection failed: {e}")
            messagebox.showerror("Error", f"Connection failed:\n{e}")
            
    def send_email(self):
        if not self.credentials:
            messagebox.showerror("Error", "Load credentials first!")
            return
            
        to_emails = self.to_entry.get().strip()
        subject = self.subject_entry.get().strip()
        body = self.body_text.get('1.0', tk.END).strip()
        from_name = self.name_entry.get().strip()
        
        if not to_emails:
            messagebox.showerror("Error", "Enter recipient email(s)!")
            return
        if not subject:
            messagebox.showerror("Error", "Enter subject!")
            return
        if not body:
            messagebox.showerror("Error", "Enter message body!")
            return
            
        # Parse recipients
        recipients = [e.strip() for e in to_emails.replace(';', ',').split(',') if e.strip()]
        
        try:
            service = build('gmail', 'v1', credentials=self.credentials)
            
            self.log(f"\nSending to {len(recipients)} recipient(s)...")
            
            success_count = 0
            for recipient in recipients:
                try:
                    msg = self.create_message(self.current_email, recipient, subject, body, from_name, self.html_var.get())
                    service.users().messages().send(userId='me', body=msg).execute()
                    self.log(f"  ✓ Sent to: {recipient}")
                    success_count += 1
                except HttpError as e:
                    self.log(f"  ✗ Failed: {recipient} - {e}")
                except Exception as e:
                    self.log(f"  ✗ Error: {recipient} - {e}")
                    
            self.log(f"\nComplete: {success_count}/{len(recipients)} sent successfully")
            
            if success_count == len(recipients):
                messagebox.showinfo("Success", f"All {success_count} email(s) sent successfully!")
            else:
                messagebox.showwarning("Partial Success", f"Sent {success_count}/{len(recipients)} emails. Check log for errors.")
                
        except Exception as e:
            self.log(f"✗ Send failed: {e}")
            messagebox.showerror("Error", f"Failed to send:\n{e}")
            
    def create_message(self, sender, to, subject, body, from_name=None, html=True):
        if html:
            msg = MIMEMultipart('alternative')
            msg['To'] = to
            msg['From'] = f"{from_name} <{sender}>" if from_name else sender
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'html'))
        else:
            msg = MIMEText(body)
            msg['To'] = to
            msg['From'] = f"{from_name} <{sender}>" if from_name else sender
            msg['Subject'] = subject
            
        return {'raw': base64.urlsafe_b64encode(msg.as_bytes()).decode()}
        
    def log(self, message):
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + '\n')
        self.log_text.see(tk.END)
        self.log_text.configure(state=tk.DISABLED)
        
    def clear(self):
        self.to_entry.delete(0, tk.END)
        self.subject_entry.delete(0, tk.END)
        self.body_text.delete('1.0', tk.END)
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.delete('1.0', tk.END)
        self.log_text.configure(state=tk.DISABLED)


if __name__ == '__main__':
    from pathlib import Path
    root = tk.Tk()
    app = GmailSenderGUI(root)
    root.mainloop()
