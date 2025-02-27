# Dynamic DNS Updater with Cloudflare



## Overview

This project is a rudimentary **Dynamic DNS (DDNS) Updater** designed to keep your **Cloudflare DNS records** in sync with your dynamically changing public IP address. The script runs inside a **Docker container**, checks your IP at a set interval, and updates Cloudflare when a change is detected. It also includes **email notifications** and **rotating logs** for improved reliability and maintainability.

---

## Features

✅ **Automatic IP Detection** – Fetches your public IP and updates Cloudflare if it changes.\
✅ **Cloudflare API Integration** – Seamlessly updates your DNS A-record on Cloudflare.\
✅ **Dockerized Deployment** – Runs in an isolated container for consistency.\
✅ **Persistent Volumes** – Stores logs and last known IP persistently.\
✅ **Email Notifications** – Sends an email when the IP is updated or if an error occurs.\
✅ **Rotating Logs** – Keeps logs manageable by automatically rotating them.

---

## Installation & Setup

### **1. Clone the Repository**

```bash
git clone git@github.com:kylecharlesbotha/ddns_update.git
cd ddns_update
```

### **2. Set Up Environment Variables**

Create a `.env` file in the project directory:

```ini
CF_API_TOKEN=your_cloudflare_api_token
CF_ZONE_ID=your_cloudflare_zone_id
DOMAIN_NAME=your_domain_name
IP_INTERVAL_CHECK=300  # Check interval in seconds

# Email Settings
SMTP_SERVER=your_smtp_server
SMTP_PORT=587
SMTP_USER=your_email@example.com
SMTP_PASSWORD=your_email_password
TO_EMAIL=recipient_email@example.com
```
## Docker compose 

```bash
docker-compose up -d
```


## Build and run container (Without docker-compose)

### **3. Build the Docker Image**

```bash
docker build -t ddns-updater .
```

### **4. Run the Container**

```bash
docker run -d --restart always --name ddns-updater-container \
    -v /home/kyle/ddns_updater:/app \
    --env-file .env \
    ddns-updater
```

### **5. Verify Container Logs**

To check if the container is running correctly:

```bash
docker logs -f ddns-updater-container
```

---

## Log Management

Logging is stored in a persistent volume at `/home/kyle/ddns_updater`.

- **Log Rotation:** To prevent excessive log size, log rotation is implemented.
- **Last Known IP:** The script saves the last detected IP to `last_ip.txt`.

To manually check logs:

```bash
tail -f /home/kyle/ddns_updater/ddns_update.log
```

---

## Troubleshooting

**1. Check if the container is running:**

```bash
docker ps
```

**2. Restart the container if needed:**

```bash
docker restart ddns-updater-container
```

**3. Check logs for errors:**

```bash
docker logs ddns-updater-container
```

**4. Stop and remove the container (if needed):**

```bash
docker stop ddns-updater-container
docker rm ddns-updater-container
```

---

## Contributions

Feel free to open an issue or submit a pull request if you have improvements!

---

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

---

🚀 **Happy Hosting!**


