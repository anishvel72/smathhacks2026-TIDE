from copy import deepcopy
from datetime import datetime, timezone


def now_iso():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


class DiveSiteStore:
    def __init__(self):
        seed_user = {
            "email": "seed@tide.local",
            "sub": "seed-user",
            "display_name": "TIDE Seed Data",
            "identifier": "seed@tide.local",
        }
        self._sites = [
            {
                "id": 1,
                "name": "Molasses Reef",
                "lat": 25.0097,
                "lng": -80.3762,
                "region": "Key Largo",
                "difficulty": "Open Water",
                "depth_ft": 35,
                "visibility_ft": 60,
                "notes": "Shallow coral formations with easy boat access.",
                "added_at": "2026-03-10T14:00:00+00:00",
                "updated_at": "2026-03-10T14:00:00+00:00",
                "added_by": seed_user,
                "updated_by": seed_user,
            },
            {
                "id": 2,
                "name": "French Reef",
                "lat": 25.0255,
                "lng": -80.3529,
                "region": "Key Largo",
                "difficulty": "Open Water",
                "depth_ft": 28,
                "visibility_ft": 55,
                "notes": "Popular reef line for survey and beginner drift dives.",
                "added_at": "2026-03-11T14:00:00+00:00",
                "updated_at": "2026-03-11T14:00:00+00:00",
                "added_by": seed_user,
                "updated_by": seed_user,
            },
            {
                "id": 3,
                "name": "Sombrero Reef",
                "lat": 24.6266,
                "lng": -81.1102,
                "region": "Marathon",
                "difficulty": "Advanced",
                "depth_ft": 42,
                "visibility_ft": 70,
                "notes": "Strong current windows; best with experienced buddies.",
                "added_at": "2026-03-12T14:00:00+00:00",
                "updated_at": "2026-03-12T14:00:00+00:00",
                "added_by": seed_user,
                "updated_by": seed_user,
            },
            {
                "id": 4,
                "name": "Looe Key",
                "lat": 24.5481,
                "lng": -81.4068,
                "region": "Lower Keys",
                "difficulty": "Open Water",
                "depth_ft": 30,
                "visibility_ft": 65,
                "notes": "High biodiversity and wide reef structure for photography.",
                "added_at": "2026-03-13T14:00:00+00:00",
                "updated_at": "2026-03-13T14:00:00+00:00",
                "added_by": seed_user,
                "updated_by": seed_user,
            },
        ]
        self._next_id = len(self._sites) + 1

    def list_sites(self):
        return deepcopy(self._sites)

    def get_site(self, site_id):
        site = next((site for site in self._sites if site["id"] == site_id), None)
        return deepcopy(site) if site else None

    def create_site(self, payload, actor):
        timestamp = now_iso()
        site = {
            "id": self._next_id,
            **payload,
            "added_at": timestamp,
            "updated_at": timestamp,
            "added_by": actor,
            "updated_by": actor,
        }
        self._sites.append(site)
        self._next_id += 1
        return deepcopy(site)

    def update_site(self, site_id, payload, actor):
        site = next((site for site in self._sites if site["id"] == site_id), None)
        if not site:
            return None

        site.update(payload)
        site["updated_at"] = now_iso()
        site["updated_by"] = actor
        return deepcopy(site)
