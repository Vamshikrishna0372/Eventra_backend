from pydantic import BaseModel, Field

class EmailRequest(BaseModel):
    email_type: str = Field(..., alias="email_type", description="Type of email (e.g., invitation, reminder, notification)")
    event_title: str = Field(..., alias="event_title", description="Title of the event")
    event_date: str = Field(..., alias="event_date", description="Date of the event")
    event_location: str = Field(..., alias="event_location", description="Location/Venue of the event")
    organizer: str = Field(..., description="Organizer name")

    class Config:
        populate_by_name = True

class EmailResponse(BaseModel):
    email_content: str = Field(..., alias="email_content", description="The AI-generated email content (Subject + Body)")
