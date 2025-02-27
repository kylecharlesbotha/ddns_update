import requests
import json
import time
import os
from dotenv import load_dotenv
import logging
from logging.handlers import RotatingFileHandler
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path

load_dotenv()

# Cloudflare API details (set these as environment variables for security)
CF_API_TOKEN = os.getenv('CF_API_TOKEN')  # Cloudflare API Token
CF_ZONE_ID = os.getenv('CF_ZONE_ID')  # Cloudflare Zone ID
DOMAIN_NAME = os.getenv('DOMAIN_NAME')  # The domain you want to update
IP_INTERVAL_CHECK = int(os.getenv('IP_INTERVAL_CHECK'))  # Interval to do check

# Email details (set these as environment variables for security)
SMTP_SERVER = os.getenv('SMTP_SERVER')  # SMTP server (e.g., smtp.gmail.com)
SMTP_PORT = os.getenv('SMTP_PORT', 587)  # SMTP server port (default is 587 for TLS)
SMTP_USER = os.getenv('SMTP_USER')  # Email address to send from
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')  # Email account password or app password
TO_EMAIL = os.getenv('TO_EMAIL')  # The recipient email address

# File to store the last known IP
IP_FILE_PATH = "last_ip.txt"

# Set up logging with rotation
log_dir = "/home/kyle/ddns_updater"  # Path to your log directory
os.makedirs(log_dir, exist_ok=True)

log_file = os.path.join(log_dir, "ddns_update.log")

# Set up logging with a rotating file handler
handler = RotatingFileHandler(
    log_file, maxBytes=10*1024*1024, backupCount=5  # Rotate after 10MB, keep 5 backups
)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)

# Set up the logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(handler)

# Send email notification for failure
def send_failure_email(subject, body):
    try:
        msg = MIMEMultipart()
        msg['From'] = SMTP_USER
        msg['To'] = TO_EMAIL
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            text = msg.as_string()
            server.sendmail(SMTP_USER, TO_EMAIL, text)
            logger.info(f"Failure email sent to {TO_EMAIL}")
    except Exception as e:
        logger.error(f"Error sending failure email: {e}")

# Send email notification for successful IP update
def send_success_email(ip):
    try:
        subject = f"{DOMAIN_NAME} DDNS Update Success: IP Updated to {ip}"
        body = f"The DNS record for {DOMAIN_NAME} has been successfully updated to the new IP: {ip}"

        msg = MIMEMultipart()
        msg['From'] = SMTP_USER
        msg['To'] = TO_EMAIL
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            text = msg.as_string()
            server.sendmail(SMTP_USER, TO_EMAIL, text)
            logger.info(f"Success email sent to {TO_EMAIL}")
    except Exception as e:
        logger.error(f"Error sending success email: {e}")

# Get public IP address
def get_public_ip():
    try:
        ip = requests.get('https://api.ipify.org').text
        logger.info(f"Current public IP: {ip}")
        return ip
    except requests.RequestException as e:
        error_msg = f"Error getting public IP: {e}"
        logger.error(error_msg)
        send_failure_email("DDNS Update Failure: Get Public IP", error_msg)
        return None

# Get DNS Record ID for the specified domain name
def get_dns_record_id():
    url = f"https://api.cloudflare.com/client/v4/zones/{CF_ZONE_ID}/dns_records"
    headers = {
        "Authorization": f"Bearer {CF_API_TOKEN}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            dns_records = response.json()["result"]
            for record in dns_records:
                if record["name"] == DOMAIN_NAME and record["type"] == "A":
                    logger.info(f"Found DNS record for {DOMAIN_NAME} with ID: {record['id']}")
                    return record["id"]
            error_msg = f"No 'A' record found for {DOMAIN_NAME}."
            logger.error(error_msg)
            send_failure_email("DDNS Update Failure: DNS Record Not Found", error_msg)
        else:
            error_msg = f"Failed to fetch DNS records: {response.status_code} - {response.text}"
            logger.error(error_msg)
            send_failure_email("DDNS Update Failure: Fetch DNS Records", error_msg)
    except requests.RequestException as e:
        error_msg = f"Error fetching DNS records: {e}"
        logger.error(error_msg)
        send_failure_email("DDNS Update Failure: Fetch DNS Records", error_msg)

    return None

# Update DNS record on Cloudflare
def update_dns(ip, record_id):
    url = f"https://api.cloudflare.com/client/v4/zones/{CF_ZONE_ID}/dns_records/{record_id}"
    headers = {
        "Authorization": f"Bearer {CF_API_TOKEN}",
        "Content-Type": "application/json",
    }
    data = {
        "type": "A",
        "name": DOMAIN_NAME,
        "content": ip,
        "ttl": 120,  # TTL in seconds
        "proxied": False  # Set to True if using Cloudflare proxy
    }

    try:
        response = requests.put(url, headers=headers, data=json.dumps(data))
        if response.status_code == 200:
            logger.info(f"Successfully updated DNS to IP: {ip}")
            send_success_email(ip)
        else:
            error_msg = f"Failed to update DNS: {response.status_code} - {response.text}"
            logger.error(error_msg)
            send_failure_email("DDNS Update Failure: Update DNS Record", error_msg)
    except requests.RequestException as e:
        error_msg = f"Error updating DNS: {e}"
        logger.error(error_msg)
        send_failure_email("DDNS Update Failure: Update DNS Record", error_msg)

# Get the last known IP from the file (or return None if file doesn't exist)
def get_last_known_ip():
    if Path(IP_FILE_PATH).exists():
        with open(IP_FILE_PATH, "r") as file:
            return file.read().strip()
    return None

# Save the current IP to a file for persistence
def save_ip_to_file(ip):
    with open(IP_FILE_PATH, "w") as file:
        file.write(ip)
        logger.info(f"Saved IP {ip} to file")

# Main function to check and update IP
def check_and_update_ip():
    logger.info(f"Initiating check and update of IP address.")
    previous_ip = get_last_known_ip()
    logger.info(f"Last known IP: {previous_ip}")

    record_id = get_dns_record_id()
    logger.info(f"DNS Record ID: {record_id}")

    if not record_id:
        logger.error("Could not find DNS record ID. Exiting...")
        send_failure_email("DDNS Update Failure: No DNS Record ID", "Could not find DNS record ID. Exiting...")
        return

    while True:
        current_ip = get_public_ip()
        
        if current_ip:
            if current_ip != previous_ip:
                logger.info(f"IP has changed: {current_ip}")
                update_dns(current_ip, record_id)
                save_ip_to_file(current_ip)
                previous_ip = current_ip
            else:
                logger.info("IP is the same, no update needed.")
        else:
            logger.error("Could not get current IP.")

        time.sleep(IP_INTERVAL_CHECK)  # Sleep for the interval before checking again

if __name__ == "__main__":
    check_and_update_ip()

