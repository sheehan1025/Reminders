#!/usr/bin/env python3
import schedule
# Need to ensure 'pip install schedule'. Not in standard library
import time
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from sqlalchemy import create_engine, Column, String, Integer, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import DeclarativeMeta, declarative_base
from datetime import datetime, timedelta

Base: DeclarativeMeta = declarative_base()


class User(Base):
    __tablename__ = "users"
    user_email = Column(String, primary_key=True)
    user_name = Column(String)
    user_password = Column(String)
    events = relationship("Event", back_populates="user")


class Event(Base):
    __tablename__ = "events"
    event_title = Column(String)
    user_email = Column(String, ForeignKey("users.user_email"))
    date_of_event = Column(Integer)
    user = relationship("User", back_populates="events")


# Database setup
engine = create_engine('sqlite:///TEST_Birthday_Reminder_2.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()


def send_email(user_email, message_content):
    """
    Function to send weekly (every Saturday at 12:01 am) autogenerated emails to a users.
    :param user_email: Email address of the recipient.
    :param message_content: Content of the email.
    """
    msg = MIMEMultipart()
    msg['From'] = 'WeeklyBirthdayReminder@gmail.com'  # temporary Team STAX gmail address
    msg['To'] = user_email
    msg['Subject'] = 'Upcoming Birthdays & Events'

    msg.attach(MIMEText(message_content, 'plain'))

    # establish connection to the mail server
    server = smtplib.SMTP('smtp.gmail.com', 587)  # Google SMTP server details
    server.starttls()
    server.login('WeeklyBirthdayEmail@gmail.com', 'TeamSTAX2023!')  # temporary Team STAX gmail and password

    server.send_message(msg)
    server.quit()


def notify_users():
    """
    Function to notify users about their upcoming events.
    It selects the upcoming events from the SQLite database, formats the message and sends the email.
    """
    users = session.query(User).all()

    # Get the current day of the year
    today = datetime.now()
    current_day = (today - datetime(today.year, 1, 1)).days + 1

    for user in users:
        # Select events from the current day to 181 days in the future
        events = session.query(Event).filter(Event.user_email == user.user_email, Event.date_of_event >= current_day,
                                             Event.date_of_event < current_day + 181).all()

        if events:
            message_content = f'Hello {user.user_name}, here are your birthday and event reminders for the next 6 months:\n'
            for event in events:
                # Convert the day of the year to a date
                # Will display as (ex. Sunday, January 1st)
                date = datetime(today.year, 1, 1) + timedelta(event.date_of_event - 1)
                day = date.day
                suffix = 'th' if 11 <= day <= 13 else {1: 'st', 2: 'nd', 3: 'rd'}.get(day % 10, 'th')
                date_str = date.strftime('%A, %B') + f" {day}{suffix}"
                message_content += f'{event.event_title}: {date_str}\n'

            send_email(user.user_email, message_content)


# Schedule the job every Saturday at 00:01
schedule.every().saturday.at("00:01").do(notify_users)

# Keep the script running
while True:
    # Check if there's a pending task
    schedule.run_pending()
    # Sleep for a second before checking again
    time.sleep(1)