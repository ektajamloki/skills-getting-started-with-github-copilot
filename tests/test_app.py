import pytest
from fastapi.testclient import TestClient
from src.app import app


class TestGetActivities:
    """Tests for GET /activities endpoint"""

    def test_get_activities_returns_all_activities(self, client):
        """Test that GET /activities returns all activities with correct structure"""
        response = client.get("/activities")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify activities list is not empty
        assert len(data) > 0
        
        # Verify expected activity names exist
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Gym Class" in data
    
    def test_activity_has_required_fields(self, client):
        """Test that each activity has all required fields"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_data in data.items():
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data
            assert isinstance(activity_data["participants"], list)
    
    def test_participants_are_strings(self, client):
        """Test that all participant entries are email strings"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_data in data.items():
            for participant in activity_data["participants"]:
                assert isinstance(participant, str)
                assert "@" in participant


class TestSignup:
    """Tests for POST /activities/{activity_name}/signup endpoint"""
    
    def test_successful_signup(self, client):
        """Test successfully signing up a new participant"""
        response = client.post(
            "/activities/Chess%20Club/signup",
            params={"email": "newstudent@mergington.edu"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "newstudent@mergington.edu" in data["message"]
        
        # Verify participant was added
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert "newstudent@mergington.edu" in activities_data["Chess Club"]["participants"]
    
    def test_signup_duplicate_participant_returns_400(self, client):
        """Test that signing up a participant twice returns 400 error"""
        # First signup
        response1 = client.post(
            "/activities/Chess%20Club/signup",
            params={"email": "duplicate@mergington.edu"}
        )
        assert response1.status_code == 200
        
        # Attempt duplicate signup
        response2 = client.post(
            "/activities/Chess%20Club/signup",
            params={"email": "duplicate@mergington.edu"}
        )
        
        assert response2.status_code == 400
        data = response2.json()
        assert "already signed up" in data["detail"]
    
    def test_signup_nonexistent_activity_returns_404(self, client):
        """Test that signing up to non-existent activity returns 404 error"""
        response = client.post(
            "/activities/Nonexistent%20Club/signup",
            params={"email": "student@mergington.edu"}
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()
    
    def test_signup_with_existing_participant(self, client):
        """Test that existing participant can be verified in participants list"""
        # Get initial state
        initial = client.get("/activities").json()
        initial_count = len(initial["Chess Club"]["participants"])
        
        # Signup new participant
        client.post(
            "/activities/Chess%20Club/signup",
            params={"email": "test123@mergington.edu"}
        )
        
        # Verify count increased
        updated = client.get("/activities").json()
        assert len(updated["Chess Club"]["participants"]) == initial_count + 1


class TestUnregister:
    """Tests for DELETE /activities/{activity_name}/unregister endpoint"""
    
    def test_successful_unregister(self, client):
        """Test successfully unregistering a participant"""
        # First, signup a participant
        client.post(
            "/activities/Chess%20Club/signup",
            params={"email": "toremove@mergington.edu"}
        )
        
        # Verify they're registered
        check1 = client.get("/activities").json()
        assert "toremove@mergington.edu" in check1["Chess Club"]["participants"]
        
        # Unregister them
        response = client.delete(
            "/activities/Chess%20Club/unregister",
            params={"email": "toremove@mergington.edu"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "toremove@mergington.edu" in data["message"]
        
        # Verify they're removed
        check2 = client.get("/activities").json()
        assert "toremove@mergington.edu" not in check2["Chess Club"]["participants"]
    
    def test_unregister_nonexistent_participant_returns_400(self, client):
        """Test that unregistering a non-registered participant returns 400 error"""
        response = client.delete(
            "/activities/Chess%20Club/unregister",
            params={"email": "notregistered@mergington.edu"}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "not registered" in data["detail"]
    
    def test_unregister_from_nonexistent_activity_returns_404(self, client):
        """Test that unregistering from non-existent activity returns 404 error"""
        response = client.delete(
            "/activities/Nonexistent%20Club/unregister",
            params={"email": "student@mergington.edu"}
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()
    
    def test_unregister_reduces_participant_count(self, client):
        """Test that unregistering reduces the participant count"""
        initial = client.get("/activities").json()
        initial_count = len(initial["Programming Class"]["participants"])
        
        # Unregister an existing participant
        client.delete(
            "/activities/Programming%20Class/unregister",
            params={"email": "emma@mergington.edu"}
        )
        
        updated = client.get("/activities").json()
        assert len(updated["Programming Class"]["participants"]) == initial_count - 1


class TestModify:
    """Tests for PUT /activities/{activity_name}/modify endpoint"""
    
    def test_successful_modify(self, client):
        """Test successfully modifying a participant's email"""
        # Signup a participant first
        client.post(
            "/activities/Debate%20Team/signup",
            params={"email": "oldmail@mergington.edu"}
        )
        
        # Modify their email
        response = client.put(
            "/activities/Debate%20Team/modify",
            params={
                "old_email": "oldmail@mergington.edu",
                "new_email": "newmail@mergington.edu"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "oldmail@mergington.edu" in data["message"]
        assert "newmail@mergington.edu" in data["message"]
        
        # Verify change was made
        activities = client.get("/activities").json()
        assert "newmail@mergington.edu" in activities["Debate Team"]["participants"]
        assert "oldmail@mergington.edu" not in activities["Debate Team"]["participants"]
    
    def test_modify_nonexistent_participant_returns_400(self, client):
        """Test that modifying non-existent participant returns 400 error"""
        response = client.put(
            "/activities/Chess%20Club/modify",
            params={
                "old_email": "nonexistent@mergington.edu",
                "new_email": "new@mergington.edu"
            }
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "not registered" in data["detail"]
    
    def test_modify_to_duplicate_email_returns_400(self, client):
        """Test that modifying to an already-registered email returns 400 error"""
        # Get two existing participants
        activities = client.get("/activities").json()
        chess_club = activities["Chess Club"]
        participant1 = chess_club["participants"][0]
        participant2 = chess_club["participants"][1]
        
        # Try to modify participant1 to participant2's email
        response = client.put(
            "/activities/Chess%20Club/modify",
            params={
                "old_email": participant1,
                "new_email": participant2
            }
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "already registered" in data["detail"]
    
    def test_modify_in_nonexistent_activity_returns_404(self, client):
        """Test that modifying in non-existent activity returns 404 error"""
        response = client.put(
            "/activities/Nonexistent%20Club/modify",
            params={
                "old_email": "old@mergington.edu",
                "new_email": "new@mergington.edu"
            }
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()
    
    def test_modify_same_email_to_itself(self, client):
        """Test attempting to modify a participant to the same email returns 400"""
        activities = client.get("/activities").json()
        email = activities["Programming Class"]["participants"][0]
        
        response = client.put(
            "/activities/Programming%20Class/modify",
            params={
                "old_email": email,
                "new_email": email
            }
        )
        
        # Should return 400 because the new email already exists (same as old)
        assert response.status_code == 400
        data = response.json()
        assert "already registered" in data["detail"]


class TestIntegration:
    """Integration tests combining multiple endpoints"""
    
    def test_signup_modify_unregister_flow(self, client):
        """Test complete flow: signup -> modify -> unregister"""
        activity = "Art%20Class"
        email1 = "artist1@mergington.edu"
        email2 = "artist2@mergington.edu"
        
        # Step 1: Signup
        signup_resp = client.post(f"/activities/{activity}/signup", params={"email": email1})
        assert signup_resp.status_code == 200
        
        # Verify signup
        activities = client.get("/activities").json()
        assert email1 in activities["Art Class"]["participants"]
        
        # Step 2: Modify
        modify_resp = client.put(
            f"/activities/{activity}/modify",
            params={"old_email": email1, "new_email": email2}
        )
        assert modify_resp.status_code == 200
        
        # Verify modify
        activities = client.get("/activities").json()
        assert email2 in activities["Art Class"]["participants"]
        assert email1 not in activities["Art Class"]["participants"]
        
        # Step 3: Unregister
        unregister_resp = client.delete(
            f"/activities/{activity}/unregister",
            params={"email": email2}
        )
        assert unregister_resp.status_code == 200
        
        # Verify unregister
        activities = client.get("/activities").json()
        assert email2 not in activities["Art Class"]["participants"]
    
    def test_multiple_signups_same_activity(self, client):
        """Test multiple participants signing up for the same activity"""
        activity = "Science%20Club"
        emails = [f"scientist{i}@mergington.edu" for i in range(3)]
        
        # Signup multiple participants
        for email in emails:
            response = client.post(
                f"/activities/{activity}/signup",
                params={"email": email}
            )
            assert response.status_code == 200
        
        # Verify all were added
        activities = client.get("/activities").json()
        for email in emails:
            assert email in activities["Science Club"]["participants"]
