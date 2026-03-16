import logging
from datetime import datetime, timedelta
from app.database.connection import get_database
from app.services.email_service import EmailService
from bson import ObjectId

async def send_event_reminders():
    """
    Checks for events happening in the next 24 hours
    and sends a reminder to all confirmed participants.
    """
    try:
        db = get_database()
        if db is None:
            logging.error("Task failed: MongoDB connection not available.")
            return
        now = datetime.utcnow()
        tomorrow_start = now + timedelta(hours=23, minutes=50) # Buffer
        tomorrow_end = now + timedelta(hours=24, minutes=10)
        
        # Example logic: if we stored date and time as strings, we need to convert or query.
        # Since date is "2026-04-15" and time is "10:00 AM" it's a bit harder to query directly.
        # So we'll fetch all 'open' events and manually check their datetime.
        cursor = db["events"].find({"status": "open"})
        events = await cursor.to_list(1000)
        
        for event in events:
            # Parse date/time
            try:
                date_str = event.get("date")
                time_str = event.get("time") # "10:00 AM"
                if not date_str or not time_str:
                    continue
                    
                # A very basic parser for time strings like "10:00 AM"
                time_format = "%I:%M %p" if "M" in time_str else "%H:%M"
                dt_str = f"{date_str} {time_str}"
                
                try:
                    event_dt = datetime.strptime(dt_str, f"%Y-%m-%d {time_format}")
                except ValueError:
                    continue # Skip if parsing fails
                    
                # Check if event is exactly ~24 hours away
                if tomorrow_start <= event_dt <= tomorrow_end:
                    # Check if reminders were already sent
                    if event.get("remindersSent"):
                        continue
                        
                    # Find all confirmed registrations
                    regs_cursor = db["registrations"].find({
                        "eventId": str(event["_id"]),
                        "registrationStatus": "confirmed"
                    })
                    registrations = await regs_cursor.to_list(1000)
                    
                    for reg in registrations:
                        user = await db["users"].find_one({"_id": ObjectId(reg["userId"])})
                        if user and user.get("email"):
                            html_content = f"""
                            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                                <h2>Reminder: {event['title']} is tomorrow!</h2>
                                <p>Hi {user['name']},</p>
                                <p>Just a quick reminder that you are registered for <strong>{event['title']}</strong> happening tomorrow at {event['time']}.</p>
                                <p><strong>Venue:</strong> {event['venue']}</p>
                                <p>Your ticket number is: {reg.get('ticketNumber', 'Available in dashboard')}</p>
                                <p>See you there!</p>
                                <p>Best,<br>Eventra Team</p>
                            </div>
                            """
                            EmailService.send_email(user["email"], f"Reminder: {event['title']}", html_content)
                            
                            # Also create an in-app notification
                            await db["notifications"].insert_one({
                                "userId": str(user["_id"]),
                                "title": "Event Reminder",
                                "message": f"⏰ Reminder: {event['title']} starts tomorrow at {event['time']}.",
                                "type": "reminder",
                                "readStatus": False,
                                "createdAt": datetime.utcnow()
                            })
                            
                    # Mark reminders as sent
                    await db["events"].update_one(
                        {"_id": event["_id"]},
                        {"$set": {"remindersSent": True}}
                    )
                    logging.info(f"Reminders sent for event: {event['title']}")
                    
            except Exception as e:
                logging.error(f"Error processing reminders for event {event.get('title')}: {e}")
                
    except Exception as e:
        logging.error(f"Error running reminder task: {e}")
