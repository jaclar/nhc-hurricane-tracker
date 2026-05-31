# NHC Hurricane Tracker (Atlantic Only) to ntfy.sh 🌀

This project is a lightweight, zero-dependency Python script that automatically monitors the National Hurricane Center (NHC) Atlantic basin RSS feed. It detects when new tropical storms or hurricanes form, or when new advisories are published, and sends immediate notifications to your phone or desktop via **ntfy.sh**.

## How It Works

1. **RSS Checking**: The script fetches the official NHC Atlantic feed (`index-at.xml`) at regular intervals.
2. **State Tracking**: It compares incoming advisories with a state file ([last_seen.json](file:///home/jaclar/projects/scratch/nhc-hurricane-tracker/last_seen.json)).
3. **Smart Notifications**:
   - **🚨 New Storms** are flagged with maximum urgency (`urgent` priority, custom emojis).
   - **🌀 Subsequent Advisories/Updates** are sent with default priority (if enabled).
4. **Stateless persistence via Git**: The script runs in **GitHub Actions** (completely free). The workflow automatically commits the updated `last_seen.json` state file back to the repository so it knows what it has already notified you about.

---

## Getting Started

### 1. Set Up Your ntfy.sh Topic
[ntfy.sh](https://ntfy.sh) is a free, open-source HTTP-based pub-sub notification service that requires **no account registration or credit card**.

1. Think of a unique, private topic name (e.g., `my-private-nhc-tracker-98234`).
2. Install the **ntfy** app on your phone (Android/iOS) or open the web interface at `https://ntfy.sh`.
3. Subscribe to your chosen topic.

### 2. Configure GitHub Secrets
1. Create a new, private or public GitHub repository.
2. Push this folder's contents to your repository.
3. Go to your repository settings on GitHub:
   - **Settings** -> **Secrets and variables** -> **Actions** -> **New repository secret**.
   - Name: `NTFY_TOPIC`
   - Value: *Your private topic name* (e.g., `my-private-nhc-tracker-98234`).

### 3. Verify Repository Permissions
GitHub Actions needs permission to commit changes back to the repository (to update `last_seen.json`).
1. In your GitHub repository, go to **Settings** -> **Actions** -> **General**.
2. Scroll down to **Workflow permissions**.
3. Select **Read and write permissions**.
4. Click **Save**.

The workflow is scheduled to run every 30 minutes. You can also trigger it manually at any time by going to the **Actions** tab in your repository, selecting the **NHC Hurricane Tracker** workflow, and clicking **Run workflow**.

---

## Local Development & Testing

You can test the script locally by running it from your terminal.

### Run a Test Check
To run the script locally, pass your topic name as an environment variable:

```bash
NTFY_TOPIC="your-test-topic" python3 check_hurricanes.py
```

### Configuration Options
You can customize the script behavior using environment variables:

| Variable | Description | Default |
| :--- | :--- | :--- |
| `NTFY_TOPIC` | Your ntfy.sh subscription topic | *Required* |
| `NOTIFY_UPDATES` | Send updates for existing storms (advisories) | `true` (set to `false` for new storms only) |
| `NTFY_SERVER` | Custom self-hosted ntfy server URL | `https://ntfy.sh` |
