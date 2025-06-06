from flask import Flask, render_template, request, redirect, flash
import smtplib
from email.message import EmailMessage
from email.utils import formataddr
import csv, os
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = 'your_secret_key'

SENDER_EMAIL = "info@3d-labs.com"
APP_PASSWORD = "QHJsM56h2Afr"
LOG_FILE = "email_log.csv"
EMAIL_INTERVAL_DAYS = 50

category_emails = {
    "Sales": ["sales@example.com"],  # Replace with actual emails
    "Support": ["support@example.com"],  # Replace with actual emails
    "Marketing": ["marketing@example.com"],  # Replace with actual emails
    "Custom": []
}

def can_send_email(recipient):
    if not os.path.exists(LOG_FILE):
        return True
    with open(LOG_FILE, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row['email'] == recipient:
                last_sent = datetime.strptime(row['timestamp'], '%Y-%m-%d')
                if datetime.now() - last_sent < timedelta(days=EMAIL_INTERVAL_DAYS):
                    return False
    return True

def log_email_sent(recipient):
    file_exists = os.path.exists(LOG_FILE)
    with open(LOG_FILE, mode='a', newline='') as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(['email', 'timestamp'])
        writer.writerow([recipient, datetime.now().strftime('%Y-%m-%d')])

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        category = request.form.get("category")
        subject = request.form.get("subject")
        message = request.form.get("message")
        file = request.files.get("attachment")
        custom_email = request.form.get("custom_email")

        if not category or not subject or not message:
            flash("All fields are required.", "error")
            return redirect("/")

        # Handle recipients based on category
        if category == "Custom":
            if not custom_email:
                flash("Custom email address is required.", "error")
                return redirect("/")
            # Split email addresses by comma and strip whitespace
            recipients = [email.strip() for email in custom_email.split(',') if email.strip()]
            if not recipients:
                flash("Please enter valid email addresses.", "error")
                return redirect("/")
        else:
            recipients = category_emails.get(category, [])

        if not recipients:
            flash("No recipients found for selected category.", "error")
            return redirect("/")

        sent_count = 0
        skipped_count = 0
        attachment_data = None
        attachment_name = None

        if file and file.filename:
            attachment_data = file.read()
            attachment_name = file.filename

        try:
            for recipient in recipients:
                if not can_send_email(recipient):
                    skipped_count += 1
                    continue

                msg = EmailMessage()
                msg["Subject"] = subject
                msg["From"] = formataddr(("3D Labs", SENDER_EMAIL))
                msg["To"] = recipient
                msg.set_content(message + "\n\n\n,\n")

                if attachment_data:
                    msg.add_attachment(attachment_data, maintype="application", subtype="octet-stream", filename=attachment_name)

                with smtplib.SMTP_SSL("smtppro.zoho.in", 465) as smtp:
                    smtp.login(SENDER_EMAIL, APP_PASSWORD)
                    smtp.send_message(msg)

                log_email_sent(recipient)
                sent_count += 1

            flash(f"Emails sent: {sent_count}, Skipped: {skipped_count}", "success")
        except Exception as e:
            flash(f"Error: {str(e)}", "error")
        return redirect("/")

    return render_template("index.html", categories=category_emails.keys())


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

