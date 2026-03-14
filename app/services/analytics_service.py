from app.database.connection import get_database
from bson import ObjectId

class AnalyticsService:
    @staticmethod
    async def get_overview():
        db = get_database()
        
        total_events = await db["events"].count_documents({})
        active_events = await db["events"].count_documents({"status": "open"})
        completed_events = await db["events"].count_documents({"status": "completed"})
        total_registrations = await db["registrations"].count_documents({})
        total_users = await db["users"].count_documents({"role": "student"})
        
        # Get category distribution
        pipeline = [
            {"$group": {"_id": "$category", "count": {"$sum": 1}}}
        ]
        category_counts = await db["events"].aggregate(pipeline).to_list(100)
        category_data = {item["_id"]: item["count"] for item in category_counts}
        
        trending_category = max(category_data, key=category_data.get) if category_data else "None"
        
        # Recent registrations (last 5)
        recent_regs_cursor = db["registrations"].find({"registrationStatus": "confirmed"}).sort("registrationDate", -1).limit(5)
        recent_regs = await recent_regs_cursor.to_list(5)
        
        recent_data = []
        for reg in recent_regs:
            user = await db["users"].find_one({"_id": ObjectId(reg["userId"])})
            event = await db["events"].find_one({"_id": ObjectId(reg["eventId"])})
            if user and event:
                recent_data.append({
                    "id": str(reg["_id"]),
                    "studentName": user["name"],
                    "eventName": event["title"],
                    "registeredAt": reg.get("registrationDate", "").isoformat() if hasattr(reg.get("registrationDate"), 'isoformat') else str(reg.get("registrationDate", ""))
                })
        
        # Get monthly trends (last 6 months)
        from datetime import datetime, timedelta
        six_months_ago = datetime.now() - timedelta(days=180)
        
        # Monthly events
        events_pipeline = [
            {"$match": {"createdAt": {"$gte": six_months_ago}}},
            {"$group": {
                "_id": {"$dateToString": {"format": "%b", "date": "$createdAt"}},
                "count": {"$sum": 1},
                "sort": {"$min": "$createdAt"}
            }},
            {"$sort": {"sort": 1}}
        ]
        events_trend = await db["events"].aggregate(events_pipeline).to_list(6)
        
        # Monthly registrations
        regs_pipeline = [
            {"$match": {"registrationDate": {"$gte": six_months_ago}}},
            {"$group": {
                "_id": {"$dateToString": {"format": "%b", "date": "$registrationDate"}},
                "count": {"$sum": 1},
                "sort": {"$min": "$registrationDate"}
            }},
            {"$sort": {"sort": 1}}
        ]
        regs_trend = await db["registrations"].aggregate(regs_pipeline).to_list(6)
        
        # Merge trends
        trends_map = {}
        for item in events_trend:
            trends_map[item["_id"]] = {"month": item["_id"], "events": item["count"], "registrations": 0}
        for item in regs_trend:
            if item["_id"] in trends_map:
                trends_map[item["_id"]]["registrations"] = item["count"]
            else:
                trends_map[item["_id"]] = {"month": item["_id"], "events": 0, "registrations": item["count"]}
        
        # Ensure we have some data even if empty
        monthly_trends = list(trends_map.values())
        if not monthly_trends:
            monthly_trends = [{"month": datetime.now().strftime("%b"), "events": 0, "registrations": 0}]

        return {
            "totalEvents": total_events,
            "activeEvents": active_events,
            "completedEvents": completed_events,
            "totalRegistrations": total_registrations,
            "totalUsers": total_users,
            "trendingCategory": trending_category,
            "categoryDistribution": category_data,
            "recentRegistrations": recent_data,
            "monthlyTrends": monthly_trends
        }

    @staticmethod
    async def get_leaderboard():
        db = get_database()
        
        # Aggregate top students by confirmed/present registrations
        pipeline = [
            {"$match": {"registrationStatus": "confirmed"}},
            {"$group": {"_id": "$userId", "events_attended": {"$sum": 1}}},
            {"$sort": {"events_attended": -1}},
            {"$limit": 10}
        ]
        
        cursor = db["registrations"].aggregate(pipeline)
        top_users_data = await cursor.to_list(10)
        
        leaderboard = []
        for index, item in enumerate(top_users_data, 1):
            user = await db["users"].find_one({"_id": ObjectId(item["_id"])})
            if user:
                leaderboard.append({
                    "rank": index,
                    "id": str(user["_id"]),
                    "name": user["name"],
                    "eventsAttended": item["events_attended"],
                    "picture": user.get("profileImage", "")
                })
        
        return leaderboard
