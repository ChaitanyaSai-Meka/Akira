import logging
from livekit.agents import function_tool, RunContext
import requests
from langchain_community.tools import DuckDuckGoSearchRun
import os
import smtplib
from email.mime.multipart import MIMEMultipart  
from email.mime.text import MIMEText
from typing import Optional
import subprocess
import os
import time
import shlex

@function_tool()
async def get_weather(
    context: RunContext, 
    city: str) -> str:
    """
    Get the current weather for a given city.
    """
    try:
        response = requests.get(
            f"https://wttr.in/{city}?format=3")
        if response.status_code == 200:
            logging.info(f"Weather for {city}: {response.text.strip()}")
            return response.text.strip()   
        else:
            logging.error(f"Failed to get weather for {city}: {response.status_code}")
            return f"Could not retrieve weather for {city}."
    except Exception as e:
        logging.error(f"Error retrieving weather for {city}: {e}")
        return f"An error occurred while retrieving weather for {city}." 

@function_tool()
async def search_web(
    context: RunContext, 
    query: str) -> str:
    """
    Search the web using DuckDuckGo.
    """
    try:
        results = DuckDuckGoSearchRun().run(tool_input=query)
        logging.info(f"Search results for '{query}': {results}")
        return results
    except Exception as e:
        logging.error(f"Error searching the web for '{query}': {e}")
        return f"An error occurred while searching the web for '{query}'."    

@function_tool()    
async def send_email(
    context: RunContext, 
    to_email: str,
    subject: str,
    message: str,
    cc_email: Optional[str] = None
) -> str:
    """
    Send an email through Gmail.
    
    Args:
        to_email: Recipient email address
        subject: Email subject line
        message: Email body content
        cc_email: Optional CC email address
    """
    try:
        # Gmail SMTP configuration
        smtp_server = "smtp.gmail.com"
        smtp_port = 587
        
        # Get credentials from environment variables
        gmail_user = os.getenv("GMAIL_USER")
        gmail_password = os.getenv("GMAIL_APP_PASSWORD")  # Use App Password, not regular password
        
        if not gmail_user or not gmail_password:
            logging.error("Gmail credentials not found in environment variables")
            return "Email sending failed: Gmail credentials not configured."
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = gmail_user
        msg['To'] = to_email
        msg['Subject'] = subject
        
        # Add CC if provided
        recipients = [to_email]
        if cc_email:
            msg['Cc'] = cc_email
            recipients.append(cc_email)
        
        # Attach message body
        msg.attach(MIMEText(message, 'plain'))
        
        # Connect to Gmail SMTP server
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls() 
        server.login(gmail_user, gmail_password)
        
        # Send email
        text = msg.as_string()
        server.sendmail(gmail_user, recipients, text)
        server.quit()
        
        logging.info(f"Email sent successfully to {to_email}")
        return f"Email sent successfully to {to_email}"
        
    except smtplib.SMTPAuthenticationError:
        logging.error("Gmail authentication failed")
        return "Email sending failed: Authentication error. Please check your Gmail credentials."
    except smtplib.SMTPException as e:
        logging.error(f"SMTP error occurred: {e}")
        return f"Email sending failed: SMTP error - {str(e)}"
    except Exception as e:
        logging.error(f"Error sending email: {e}")
        return f"An error occurred while sending email: {str(e)}"

APP_ALIASES = {
    "whatsapp": "WhatsApp",
    "arc": "Arc",
    "safari": "Safari",
    "chrome": "Google Chrome",
    "spotify": "Spotify",
    "notes": "Notes",
    "terminal": "Terminal",
    "vscode": "Visual Studio Code",
    "finder": "Finder",
    "slack": "Slack",
}

APP_LOCATIONS = [
    "/Applications",
    "/System/Applications",
    os.path.expanduser("~/Applications")
]


def find_app_path(app_name: str) -> Optional[str]:
    """
    Try to locate the app using known folders first, then fallback to Spotlight.
    """
    for base in APP_LOCATIONS:
        full_path = os.path.join(base, f"{app_name}.app")
        if os.path.exists(full_path):
            return full_path

    try:
        result = subprocess.run(
            ["mdfind", f'kMDItemKind == "Application" && kMDItemDisplayName == "{app_name}"'],
            capture_output=True,
            text=True
        )
        paths = result.stdout.strip().split("\n")
        for path in paths:
            if path.endswith(f"{app_name}.app") and os.path.exists(path):
                return path
    except Exception as e:
        print(f"[ERROR] mdfind failed: {e}")
    
    return None


@function_tool()
async def open_app_or_website(
    context: RunContext,
    app_name: str,
    website: Optional[str] = None
) -> str:
    try:
        normalized_app = APP_ALIASES.get(app_name.lower(), app_name)
        app_path = find_app_path(normalized_app)

        if not app_path:
            return f"Couldn’t find app named '{normalized_app}' in known locations."

        subprocess.Popen(["open", shlex.quote(app_path)], shell=True)
        time.sleep(2)

        if website:
            subprocess.Popen(["open", website])
            return f"Opened {normalized_app} from path: {app_path} and navigated to {website}"

        return f"Opened {normalized_app} from path: {app_path}"

    except Exception as e:
        return f"Error opening {app_name}: {str(e)}"
